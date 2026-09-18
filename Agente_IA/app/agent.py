from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from groq import APIConnectionError, AuthenticationError, RateLimitError
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

from app.config import Settings
from app.memory import ConversationMemory
from app.tools import TOOLS, TOOLS_BY_NAME, verificar_compatibilidad


SYSTEM_PROMPT = """Eres CompraTech, un asistente conversacional especializado en la compra de
perifericos: audifonos, teclados, ratones, monitores, webcams, microfonos, controles, bocinas y
accesorios relacionados. Responde de forma natural, amable y personalizada en espanol.

Interpreta la categoria, el presupuesto, el uso principal, la plataforma y las preferencias del
usuario. No contestes con una plantilla fija. Explica que caracteristicas importan para su caso,
compara alternativas cuando sea util y termina con una recomendacion concreta. Si faltan datos,
haz una o dos preguntas breves, pero ofrece mientras tanto una primera orientacion que sea util.
Manten el contexto para responder seguimientos sin volver a pedir lo que el usuario ya dijo.

Puedes mencionar modelos como ejemplos basados en conocimiento general, pero no afirmes que un
precio, existencia, promocion o especificacion reciente esta confirmado. Indica que debe validar el
precio y la ficha del fabricante antes de comprar. El sistema orienta; no compra ni procesa pagos.
Usa la herramienta verificar_compatibilidad cuando la combinacion de periferico, plataforma y tipo
de conexion pueda causar incompatibilidades. Integra su resultado en una respuesta razonada, no lo
copies mecanicamente y nunca contradigas sus restricciones. No inventes conectividad, certificacion
o compatibilidad de un modelo. Si no estas seguro, recomienda el tipo de producto y los criterios
de busqueda en vez de atribuirle una funcion concreta. Para Xbox, solo considera inalambrico un
modelo cuando su variante o ficha indique expresamente compatibilidad con Xbox; Bluetooth generico
o un dongle USB cualquiera no son prueba suficiente. No solicites contrasenas, tarjetas ni otros
datos sensibles. Esta entrega no usa RAG, catalogo en vivo ni Internet. Procura responder en menos
de 300 palabras.

Limite de dominio obligatorio: solo puedes conversar sobre perifericos, su compra, comparacion,
uso, configuracion basica, ergonomia, presupuesto y compatibilidad. Si el usuario pregunta por
cualquier otro tema, no lo respondas aunque conozcas la respuesta. Explica brevemente que tu
especialidad son los perifericos y ayudalo a retomar ese tema.
"""


PERIPHERAL_TERMS = (
    "periferico", "audifono", "auricular", "headset", "teclado", "mouse", "raton",
    "monitor", "pantalla", "webcam", "camara web", "microfono", "control", "gamepad",
    "joystick", "bocina", "altavoz", "impresora", "scanner", "tableta grafica",
    "volante", "dock", "adaptador", "hub usb", "usb", "bluetooth", "inalambrico",
    "mecanico", "dpi", "latencia", "compatibilidad", "compatible",
)

SHOPPING_TERMS = (
    "comprar", "compra", "recomienda", "recomendacion", "presupuesto", "precio",
    "pesos", "barato", "economico", "comparar",
)

FOLLOW_UP_TERMS = (
    "de esos", "de esas", "cual elegirias", "cual conviene", "el primero",
    "el segundo", "la primera", "la segunda", "y si", "comparalos", "mas barato",
    "mas comodo", "con cable", "sin cable",
)


@dataclass
class AgentResult:
    response: str
    tools_used: list[str]


class ShoppingAssistantAgent:
    """Agente LangChain de compras con tool calling y memoria por sesion."""

    def __init__(self, settings: Settings, memory: ConversationMemory) -> None:
        self.settings = settings
        self.memory = memory
        self._llm = None
        if settings.provider == "groq":
            self._llm = ChatGroq(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                temperature=0.65,
                max_tokens=settings.max_output_tokens,
            ).bind_tools(TOOLS)

    def chat(self, message: str, session_id: str) -> AgentResult:
        history = self.memory.get(session_id)
        if not self._is_in_scope(message, history):
            response = (
                "Solo puedo ayudarte con la compra y eleccion de perifericos, como audifonos, "
                "teclados, ratones, monitores, webcams, microfonos o controles. Retomemos ese "
                "tema: ¿que periferico buscas, para que lo usaras y cual es tu presupuesto?"
            )
            self.memory.add_many(
                session_id,
                [HumanMessage(content=message), AIMessage(content=response)],
            )
            return AgentResult(response=response, tools_used=[])

        if self.settings.provider == "mock":
            return self._mock_chat(message, session_id)
        try:
            return self._groq_chat(message, session_id)
        except RateLimitError:
            return AgentResult(
                response=(
                    "Groq alcanzo temporalmente el limite de uso de tu cuenta. "
                    "Espera alrededor de un minuto e intenta de nuevo con el mismo mensaje."
                ),
                tools_used=[],
            )
        except AuthenticationError:
            return AgentResult(
                response=(
                    "No pude autenticarme con Groq. Revisa GROQ_API_KEY o API_KEY_GROQ "
                    "en tu archivo .env."
                ),
                tools_used=[],
            )
        except APIConnectionError:
            return AgentResult(
                response=(
                    "No pude conectarme con Groq. Revisa tu conexion a Internet e intenta "
                    "nuevamente."
                ),
                tools_used=[],
            )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text.lower())
        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

    @classmethod
    def _is_in_scope(cls, message: str, history: list[object]) -> bool:
        text = cls._normalize(message)
        if any(term in text for term in PERIPHERAL_TERMS):
            return True
        if any(greeting in text for greeting in ("hola", "buenas", "que puedes hacer")):
            return True
        if history and any(term in text for term in FOLLOW_UP_TERMS + SHOPPING_TERMS):
            return True
        return False

    def _groq_chat(self, message: str, session_id: str) -> AgentResult:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        messages.extend(self.memory.get(session_id))
        user_message = HumanMessage(content=message)
        messages.append(user_message)
        new_messages = [user_message]
        tools_used: list[str] = []

        for _ in range(3):
            assistant = self._llm.invoke(messages)
            messages.append(assistant)
            new_messages.append(assistant)
            if not assistant.tool_calls:
                text = str(assistant.content).strip() or "No pude generar una respuesta."
                self.memory.add_many(session_id, new_messages)
                return AgentResult(response=text, tools_used=tools_used)

            for call in assistant.tool_calls:
                tool_name = call["name"]
                selected_tool = TOOLS_BY_NAME.get(tool_name)
                if selected_tool is None:
                    tool_output = f"Herramienta no disponible: {tool_name}"
                else:
                    tool_output = selected_tool.invoke(call.get("args", {}))
                    tools_used.append(tool_name)
                tool_message = ToolMessage(
                    content=str(tool_output), tool_call_id=call["id"]
                )
                messages.append(tool_message)
                new_messages.append(tool_message)

        fallback = "No pude completar la consulta despues de varios intentos de herramientas."
        self.memory.add_many(session_id, new_messages + [AIMessage(content=fallback)])
        return AgentResult(response=fallback, tools_used=tools_used)

    def _mock_chat(self, message: str, session_id: str) -> AgentResult:
        """Respuesta determinista para demos y pruebas sin usar una API externa."""
        lowered = message.lower()
        tools_used: list[str] = []

        if any(word in lowered for word in ("compatible", "compatibilidad", "funciona con")):
            response = verificar_compatibilidad.invoke(
                {
                    "periferico": "periferico indicado",
                    "plataforma": message,
                    "conexion": message,
                }
            )
            tools_used.append("verificar_compatibilidad")
        elif any(word in lowered for word in ("hola", "buenas", "ayuda")):
            response = (
                "Hola, soy CompraTech. El modo de prueba esta activo, asi que no puedo generar "
                "una recomendacion con el LLM. Configura Groq para conversar libremente."
            )
        else:
            response = (
                "El modo de prueba esta activo. Para obtener una recomendacion generada por IA, "
                "usa AGENT_PROVIDER=groq con tu clave y modelo configurados."
            )

        self.memory.add_many(
            session_id,
            [HumanMessage(content=message), AIMessage(content=response)],
        )
        return AgentResult(response=response, tools_used=tools_used)

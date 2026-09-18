# Asistente inteligente de compras de perifericos

Prototipo del Entregable 1 descrito en el documento del proyecto. Incluye un agente
conversacional con LangChain, memoria corta por sesion, una tool de compatibilidad y un
microservicio FastAPI con interfaz web. Su finalidad es orientar al usuario para elegir perifericos
de acuerdo con su categoria, presupuesto, uso, plataforma y preferencias. La interfaz incluye un
bot animado, indicador de respuesta y lectura por voz desde el navegador.

El sistema no realiza compras, no procesa pagos y no consulta precios o existencias en tiempo
real. Tampoco incluye RAG, base vectorial, Django ni arquitectura multiagente, porque corresponden
a etapas posteriores.

## Estructura

```text
Sistema_ayuda_videojuego/
|-- app/
|   |-- agent.py       # Agente LangChain y prompt de compras
|   |-- config.py      # Variables de entorno y limites del LLM
|   |-- main.py        # Microservicio FastAPI
|   |-- memory.py      # Memoria temporal por session_id
|   |-- schemas.py     # Contratos de entrada y salida
|   `-- tools.py       # Verificacion orientativa de compatibilidad
|-- frontend/
|   |-- index.html     # Interfaz del chat
|   |-- styles.css     # Diseno responsive y animaciones
|   |-- app.js         # Conexion con /chat y voz del bot
|   `-- bot-compratech.png
|-- tests/test_api.py
|-- cli.py
|-- requirements.txt
`-- .env.example
```

## Instalacion en Windows PowerShell

```powershell
cd "C:\Users\edgar\Documents\AgentesIA
python -m venv .venv
.\.venv\Scripts\Activate.ps1

(.venv) PS "C:\Users\edgar\Documents\AgentesIA
pip install groq
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

En este workspace el proyecto puede reutilizar `API_KEY_GROQ` del agente anterior. Para una
instalacion independiente, completa `GROQ_API_KEY` en el archivo `.env`.

## Probar por terminal

```powershell
python cli.py
```

Ejemplo de conversacion:

```text
Tu: Busco audifonos inalambricos para jugar en Xbox y tengo 1500 pesos.
CompraTech: ...
Tu: Prefiero comodidad y no me importa que no tengan RGB. ¿Cual elegirias?
CompraTech: ...
```

## Probar el microservicio

```powershell
uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000` para usar el chat web. La documentacion interactiva de la API sigue
disponible en `http://127.0.0.1:8000/docs`. Tambien puedes enviar una solicitud desde otra terminal:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/chat `
  -ContentType 'application/json' `
  -Body '{"message":"Busco un teclado mecanico silencioso para programar, presupuesto 1800 pesos","session_id":"comprador-01"}'
```

Conserva el mismo `session_id` para que el agente recuerde presupuesto y preferencias durante la
conversacion.

Endpoints disponibles:

- `GET /health`: comprueba el estado del servicio.
- `POST /chat`: envia una solicitud de compra en lenguaje natural.
- `DELETE /sessions/{session_id}`: borra la memoria temporal de esa conversacion.

## Configuracion de Groq

```dotenv
AGENT_PROVIDER=groq
GROQ_API_KEY=tu_clave
GROQ_MODEL=qwen/qwen3.8-27b
GROQ_MAX_OUTPUT_TOKENS=500
MAX_HISTORY_MESSAGES=12
```

El limite de salida evita exceder la cuota por minuto del prototipo. Nunca publiques el archivo
`.env` ni solicites al usuario datos bancarios.

## Ejecutar pruebas

```powershell
pytest -q
```

Las pruebas usan el modo `mock`, por lo que no consumen tokens. Este modo solo valida el contrato
de la API; las recomendaciones naturales se generan con `AGENT_PROVIDER=groq`.

## Alcance de las recomendaciones

El agente puede orientar sobre audifonos, teclados, ratones, monitores, webcams, microfonos,
controles, bocinas y accesorios. Las recomendaciones se basan en conocimiento general del LLM.
Como esta entrega no incorpora catalogo ni RAG, el usuario debe confirmar precio, existencia,
garantia, compatibilidad y especificaciones en la ficha oficial antes de comprar.

El dominio esta restringido a perifericos. Si el usuario pregunta por cocina, noticias, tareas
escolares, videojuegos u otro tema ajeno, el servicio no responde esa consulta y lo invita a
retomar la eleccion, comparacion, compatibilidad o uso de perifericos.

from __future__ import annotations

from langchain_core.tools import tool


@tool
def verificar_compatibilidad(
    periferico: str,
    plataforma: str,
    conexion: str,
) -> str:
    """Orienta sobre compatibilidad de un periferico segun plataforma y conexion."""
    device = periferico.strip().lower()
    platform = plataforma.strip().lower()
    connection = conexion.strip().lower()

    if "xbox" in platform:
        if "bluetooth" in connection:
            return (
                "Xbox normalmente no acepta audio Bluetooth generico de forma directa. "
                "Conviene buscar compatibilidad o licencia explicita para Xbox, conexion "
                "de 3.5 mm al control o un adaptador compatible. Restriccion: no recomiendes "
                "un modelo Bluetooth-only ni afirmes que un dongle USB generico funciona. "
                "La ficha debe mencionar explicitamente compatibilidad con Xbox."
            )
        return (
            "Verifica que el fabricante indique compatibilidad explicita con Xbox. En "
            "audifonos y controles, el tipo de enlace propietario puede ser determinante."
        )

    if any(value in platform for value in ("playstation", "ps5", "ps4")):
        if "bluetooth" in connection and any(
            value in device for value in ("audif", "headset", "auricular")
        ):
            return (
                "PlayStation suele limitar los audifonos Bluetooth genericos. Prefiere un "
                "modelo con receptor USB compatible o conexion de 3.5 mm al control."
            )
        return (
            "Comprueba que el empaque o la ficha del fabricante indique compatibilidad con "
            "tu version de PlayStation y que el puerto requerido este disponible."
        )

    if "switch" in platform or "nintendo" in platform:
        return (
            "Nintendo Switch admite distintos perifericos segun se use en modo portatil o "
            "en dock. Verifica USB-C, USB-A del dock, Bluetooth y soporte de microfono por "
            "separado antes de comprar."
        )

    if any(value in platform for value in ("pc", "laptop", "computadora")):
        return (
            "En PC revisa el puerto fisico disponible, el sistema operativo, controladores "
            "del fabricante y si las funciones avanzadas requieren software adicional. "
            "La conexion indicada parece viable, pero debe confirmarse en la ficha oficial."
        )

    return (
        f"Para confirmar {periferico} por {conexion} en {plataforma}, revisa puertos, version "
        "del sistema, controladores y la lista oficial de equipos compatibles del fabricante."
    )


TOOLS = [verificar_compatibilidad]
TOOLS_BY_NAME = {item.name: item for item in TOOLS}

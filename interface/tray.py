from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from core import arranque

COLORES = {
    "escuchando": "#2ecc71",  # verde
    "procesando": "#f39c12",  # naranja
    "inactiva": "#95a5a6",    # gris
}
TEXTOS = {
    "escuchando": "escuchando",
    "procesando": "procesando una orden",
    "inactiva": "inactiva",
}


def _crear_icono(color):
    """Dibuja un círculo de color (no hacen falta archivos de imagen)."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(pixmap)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    pintor.setPen(Qt.PenStyle.NoPen)
    pintor.setBrush(QColor(color))
    pintor.drawEllipse(6, 6, 52, 52)
    pintor.end()
    return QIcon(pixmap)


class Bandeja(QObject):
    """Icono junto al reloj. Otros hilos le avisan con las señales, que son seguras."""

    estado_cambiado = Signal(str)  # "escuchando", "procesando" o "inactiva"
    mensaje = Signal(str)          # texto para una notificación

    def __init__(self, al_cambiar_microfono, al_salir):
        super().__init__()
        self._iconos = {nombre: _crear_icono(color) for nombre, color in COLORES.items()}

        self._icono = QSystemTrayIcon(self._iconos["inactiva"])
        self._icono.setToolTip("Luna: iniciando…")

        self._menu = QMenu()
        self._accion_estado = QAction("Luna: iniciando…")
        self._accion_estado.setEnabled(False)

        self._accion_microfono = QAction("Micrófono activado")
        self._accion_microfono.setCheckable(True)
        self._accion_microfono.setChecked(True)
        self._accion_microfono.toggled.connect(al_cambiar_microfono)

        self._accion_inicio = QAction("Iniciar con Windows")
        self._accion_inicio.setCheckable(True)
        self._accion_inicio.setChecked(arranque.activado())
        self._accion_inicio.toggled.connect(self._cambiar_inicio)

        self._accion_salir = QAction("Salir")
        self._accion_salir.triggered.connect(al_salir)

        self._menu.addAction(self._accion_estado)
        self._menu.addSeparator()
        self._menu.addAction(self._accion_microfono)
        self._menu.addAction(self._accion_inicio)
        self._menu.addSeparator()
        self._menu.addAction(self._accion_salir)
        self._icono.setContextMenu(self._menu)

        self.estado_cambiado.connect(self._aplicar_estado)
        self.mensaje.connect(self._mostrar_mensaje)
        self._icono.show()

    def _aplicar_estado(self, estado):
        self._icono.setIcon(self._iconos[estado])
        texto = f"Luna: {TEXTOS[estado]}"
        self._icono.setToolTip(texto)
        self._accion_estado.setText(texto)

    def _mostrar_mensaje(self, texto):
        self._icono.showMessage("Luna", texto, QSystemTrayIcon.MessageIcon.Information, 3000)

    def _cambiar_inicio(self, activo):
        try:
            if activo:
                arranque.activar()
            else:
                arranque.desactivar()
        except OSError as error:
            print(f"No se pudo cambiar el inicio con Windows: {error}")
            self._accion_inicio.blockSignals(True)
            self._accion_inicio.setChecked(not activo)
            self._accion_inicio.blockSignals(False)
import os
from PyQt6.QtCore import QThread, pyqtSignal
from Documents.documentación.latex_report_generator import generar_reporte_entrega_latex, limpiar_archivos_temporales, escape_latex


class ReportGenerationThread(QThread):
    finished = pyqtSignal(str, str)  # id_entrega, pdf_path
    error = pyqtSignal(str)

    def __init__(self, data, template_path, output_dir):
        super().__init__()
        self.data = data
        self.template_path = template_path
        self.output_dir = output_dir

    def run(self):
        try:
            success, log = generar_reporte_entrega_latex(
                self.data, self.template_path, self.output_dir
            )
            if not success:
                self.error.emit(f"Error LaTeX:\n{log}")
                return
            limpiar_archivos_temporales(self.output_dir)
            pdf_path = os.path.join(
                self.output_dir, f"reporte_{self.data['id_entrega']}.pdf")
            self.finished.emit(self.data['id_entrega'], pdf_path)
        except Exception as e:
            self.error.emit(f"Error inesperado:\n{str(e)}")

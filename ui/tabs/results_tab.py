"""
Pestaña de resultados de búsqueda de precios.

Este módulo proporciona la interfaz para visualizar, filtrar y exportar
los resultados de las búsquedas de precios de hoteles.
"""

import os
import sys
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from ui.utils.theme import FUENTES, TAMANOS, TemaMode, obtener_tema


class ResultsTab(ctk.CTkFrame):
    """
    Pestaña de resultados de búsqueda.

    Características:
    - Panel resumen con métricas (total, con precio, sin precio)
    - Barras visuales de desglose por proveedor
    - Tabla de resultados ordenable
    - Filtros (con precio / sin precio / todos)
    - Exportar a Excel
    - Copiar al portapapeles
    """

    # Colores por proveedor
    COLORES_PROVEEDORES = {
        "xotelo": "#3498db",
        "serpapi": "#9b59b6",
        "apify": "#e67e22",
        "amadeus": "#1abc9c",
        "cache": "#95a5a6",
    }

    def __init__(
        self, master: ctk.CTkFrame, modo_tema: TemaMode = "dark", **kwargs
    ) -> None:
        """
        Inicializa la pestaña de resultados.

        Args:
            master: Widget padre.
            modo_tema: Modo de tema ("dark" o "light").
        """
        self.modo_tema = modo_tema
        self.tema = obtener_tema(modo_tema)

        super().__init__(master, fg_color="transparent", **kwargs)

        # Datos
        self._resultados: List[Dict] = []
        self._resultados_filtrados: List[Dict] = []
        self._filtro_actual = "todos"
        self._orden_columna = "hotel"
        self._orden_ascendente = True

        # Configurar layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Crear secciones
        self._crear_seccion_resumen()
        self._crear_seccion_filtros()
        self._crear_seccion_tabla()

    def _crear_seccion_resumen(self) -> None:
        """Crea la sección de resumen con métricas."""
        self.frame_resumen = ctk.CTkFrame(
            self,
            fg_color=self.tema["fondo_secundario"],
            corner_radius=10,
        )
        self.frame_resumen.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Título
        ctk.CTkLabel(
            self.frame_resumen,
            text="Resumen de Resultados",
            font=FUENTES.get("encabezado", ("Segoe UI", 14, "bold")),
            text_color=self.tema["texto_principal"],
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Frame de métricas
        frame_metricas = ctk.CTkFrame(
            self.frame_resumen,
            fg_color=self.tema["fondo_principal"],
            corner_radius=8,
        )
        frame_metricas.pack(fill="x", padx=15, pady=(0, 15))

        for i in range(5):
            frame_metricas.grid_columnconfigure(i, weight=1)

        metricas = [
            ("total", "Total", self.tema["texto_principal"]),
            ("con_precio", "Con Precio", self.tema["estados"]["exito"]),
            ("sin_precio", "Sin Precio", self.tema["estados"]["error"]),
            ("precio_min", "Precio Mín", self.tema["estados"]["info"]),
            ("precio_max", "Precio Máx", self.tema["estados"]["warning"]),
        ]

        self._labels_metricas: Dict[str, ctk.CTkLabel] = {}

        for col, (key, label, color) in enumerate(metricas):
            frame = ctk.CTkFrame(frame_metricas, fg_color="transparent")
            frame.grid(row=0, column=col, padx=10, pady=10)

            valor_label = ctk.CTkLabel(
                frame,
                text="0" if "precio" not in key else "$0.00",
                font=FUENTES.get("subtitulo", ("Segoe UI", 18, "bold")),
                text_color=color,
            )
            valor_label.pack()

            ctk.CTkLabel(
                frame,
                text=label,
                font=FUENTES.get("pequena", ("Segoe UI", 10)),
                text_color=self.tema["texto_secundario"],
            ).pack()

            self._labels_metricas[key] = valor_label

        # Barras de proveedores
        frame_proveedores = ctk.CTkFrame(self.frame_resumen, fg_color="transparent")
        frame_proveedores.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            frame_proveedores,
            text="Distribución por Proveedor:",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=self.tema["texto_principal"],
        ).pack(anchor="w", pady=(0, 5))

        self._frame_barras_proveedores = ctk.CTkFrame(
            frame_proveedores,
            fg_color=self.tema["fondo_principal"],
            corner_radius=6,
            height=30,
        )
        self._frame_barras_proveedores.pack(fill="x")
        self._frame_barras_proveedores.pack_propagate(False)

    def _crear_seccion_filtros(self) -> None:
        """Crea la sección de filtros y acciones."""
        self.frame_filtros = ctk.CTkFrame(
            self,
            fg_color=self.tema["fondo_secundario"],
            corner_radius=10,
        )
        self.frame_filtros.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        frame_inner = ctk.CTkFrame(self.frame_filtros, fg_color="transparent")
        frame_inner.pack(fill="x", padx=15, pady=10)

        # Filtros
        ctk.CTkLabel(
            frame_inner,
            text="Filtrar:",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=self.tema["texto_principal"],
        ).pack(side="left", padx=(0, 10))

        self.var_filtro = ctk.StringVar(value="todos")

        filtros = [
            ("Todos", "todos"),
            ("Con Precio", "con_precio"),
            ("Sin Precio", "sin_precio"),
        ]

        for texto, valor in filtros:
            radio = ctk.CTkRadioButton(
                frame_inner,
                text=texto,
                variable=self.var_filtro,
                value=valor,
                font=FUENTES.get("normal", ("Segoe UI", 12)),
                text_color=self.tema["texto_principal"],
                command=self._aplicar_filtro,
            )
            radio.pack(side="left", padx=10)

        # Botones de acción
        self.boton_copiar = ctk.CTkButton(
            frame_inner,
            text="📋 Copiar",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            fg_color=self.tema["acento"],
            hover_color=self.tema["acento_hover"],
            width=100,
            command=self._copiar_portapapeles,
        )
        self.boton_copiar.pack(side="right", padx=(10, 0))

        self.boton_exportar = ctk.CTkButton(
            frame_inner,
            text="📥 Exportar Excel",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            fg_color=self.tema["estados"]["exito"],
            hover_color="#27ae60",
            width=130,
            command=self._exportar_excel,
        )
        self.boton_exportar.pack(side="right")

    def _crear_seccion_tabla(self) -> None:
        """Crea la sección de tabla de resultados."""
        self.frame_tabla = ctk.CTkFrame(
            self,
            fg_color=self.tema["fondo_secundario"],
            corner_radius=10,
        )
        self.frame_tabla.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Encabezado
        frame_header = ctk.CTkFrame(
            self.frame_tabla,
            fg_color=self.tema["fondo_principal"],
            corner_radius=0,
        )
        frame_header.pack(fill="x", padx=10, pady=(10, 0))

        columnas = [
            ("#", 40, "center"),
            ("Hotel", 300, "w"),
            ("Precio", 100, "e"),
            ("Moneda", 60, "center"),
            ("Proveedor", 100, "center"),
            ("Check-in", 100, "center"),
            ("Check-out", 100, "center"),
        ]

        self._header_labels: List[ctk.CTkLabel] = []

        for texto, ancho, anchor in columnas:
            label = ctk.CTkLabel(
                frame_header,
                text=texto,
                font=FUENTES.get("encabezado", ("Segoe UI", 12, "bold")),
                text_color=self.tema["texto_principal"],
                width=ancho,
                anchor=anchor,
            )
            label.pack(side="left", padx=5, pady=8)
            self._header_labels.append(label)

            # Hacer clickeable para ordenar
            if texto not in ["#"]:
                label.bind(
                    "<Button-1>", lambda e, col=texto.lower(): self._ordenar_por(col)
                )
                label.configure(cursor="hand2")

        # Scrollable frame para filas
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.frame_tabla,
            fg_color="transparent",
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Label para cuando no hay resultados
        self.label_sin_resultados = ctk.CTkLabel(
            self.scroll_frame,
            text="No hay resultados para mostrar.\nEjecute una búsqueda en la pestaña 'Ejecutar'.",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=self.tema["texto_secundario"],
        )

    def _crear_fila(self, idx: int, resultado: Dict) -> ctk.CTkFrame:
        """Crea una fila de resultado."""
        color_fondo = (
            self.tema["fondo_principal"]
            if idx % 2 == 0
            else self.tema["fondo_secundario"]
        )

        fila = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=color_fondo,
            corner_radius=0,
        )

        # Número
        ctk.CTkLabel(
            fila,
            text=str(idx + 1),
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=self.tema["texto_secundario"],
            width=40,
            anchor="center",
        ).pack(side="left", padx=5, pady=6)

        # Hotel
        ctk.CTkLabel(
            fila,
            text=resultado.get("hotel", "")[:40],
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=self.tema["texto_principal"],
            width=300,
            anchor="w",
        ).pack(side="left", padx=5, pady=6)

        # Precio
        precio = resultado.get("precio")
        precio_texto = f"${precio:.2f}" if precio else "-"
        precio_color = (
            self.tema["estados"]["exito"] if precio else self.tema["texto_secundario"]
        )

        ctk.CTkLabel(
            fila,
            text=precio_texto,
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=precio_color,
            width=100,
            anchor="e",
        ).pack(side="left", padx=5, pady=6)

        # Moneda
        ctk.CTkLabel(
            fila,
            text=resultado.get("moneda") or "-",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=self.tema["texto_secundario"],
            width=60,
            anchor="center",
        ).pack(side="left", padx=5, pady=6)

        # Proveedor
        proveedor = resultado.get("proveedor") or "-"
        proveedor_color = self.COLORES_PROVEEDORES.get(
            proveedor.lower() if proveedor != "-" else "", self.tema["texto_secundario"]
        )

        ctk.CTkLabel(
            fila,
            text=proveedor.capitalize() if proveedor != "-" else "-",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=proveedor_color,
            width=100,
            anchor="center",
        ).pack(side="left", padx=5, pady=6)

        # Check-in
        ctk.CTkLabel(
            fila,
            text=resultado.get("check_in") or "-",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=self.tema["texto_secundario"],
            width=100,
            anchor="center",
        ).pack(side="left", padx=5, pady=6)

        # Check-out
        ctk.CTkLabel(
            fila,
            text=resultado.get("check_out") or "-",
            font=FUENTES.get("normal", ("Segoe UI", 12)),
            text_color=self.tema["texto_secundario"],
            width=100,
            anchor="center",
        ).pack(side="left", padx=5, pady=6)

        return fila

    def cargar_resultados(self, resultados: List[Dict]) -> None:
        """
        Carga resultados de búsqueda.

        Args:
            resultados: Lista de diccionarios con resultados.
        """
        self._resultados = resultados
        self._aplicar_filtro()
        self._actualizar_metricas()
        self._actualizar_barras_proveedores()

    def _aplicar_filtro(self) -> None:
        """Aplica el filtro actual y actualiza la tabla."""
        filtro = self.var_filtro.get()
        self._filtro_actual = filtro

        if filtro == "con_precio":
            self._resultados_filtrados = [
                r for r in self._resultados if r.get("precio")
            ]
        elif filtro == "sin_precio":
            self._resultados_filtrados = [
                r for r in self._resultados if not r.get("precio")
            ]
        else:
            self._resultados_filtrados = self._resultados.copy()

        self._actualizar_tabla()

    def _ordenar_por(self, columna: str) -> None:
        """Ordena los resultados por una columna."""
        if self._orden_columna == columna:
            self._orden_ascendente = not self._orden_ascendente
        else:
            self._orden_columna = columna
            self._orden_ascendente = True

        key_map = {
            "hotel": lambda x: x.get("hotel", "").lower(),
            "precio": lambda x: x.get("precio") or 0,
            "moneda": lambda x: x.get("moneda") or "",
            "proveedor": lambda x: x.get("proveedor") or "",
            "check-in": lambda x: x.get("check_in") or "",
            "check-out": lambda x: x.get("check_out") or "",
        }

        key_func = key_map.get(columna, lambda x: "")
        self._resultados_filtrados.sort(
            key=key_func, reverse=not self._orden_ascendente
        )
        self._actualizar_tabla()

    def _actualizar_tabla(self) -> None:
        """Actualiza la visualización de la tabla."""
        # Limpiar filas existentes
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self._resultados_filtrados:
            self.label_sin_resultados = ctk.CTkLabel(
                self.scroll_frame,
                text="No hay resultados para mostrar.",
                font=FUENTES.get("normal", ("Segoe UI", 12)),
                text_color=self.tema["texto_secundario"],
            )
            self.label_sin_resultados.pack(pady=50)
            return

        # Crear filas
        for idx, resultado in enumerate(self._resultados_filtrados):
            fila = self._crear_fila(idx, resultado)
            fila.pack(fill="x", pady=1)

    def _actualizar_metricas(self) -> None:
        """Actualiza las métricas del resumen."""
        total = len(self._resultados)
        con_precio = sum(1 for r in self._resultados if r.get("precio"))
        sin_precio = total - con_precio

        precios = [r.get("precio") for r in self._resultados if r.get("precio")]
        precio_min = min(precios) if precios else 0
        precio_max = max(precios) if precios else 0

        self._labels_metricas["total"].configure(text=str(total))
        self._labels_metricas["con_precio"].configure(text=str(con_precio))
        self._labels_metricas["sin_precio"].configure(text=str(sin_precio))
        self._labels_metricas["precio_min"].configure(text=f"${precio_min:.2f}")
        self._labels_metricas["precio_max"].configure(text=f"${precio_max:.2f}")

    def _actualizar_barras_proveedores(self) -> None:
        """Actualiza las barras de distribución por proveedor."""
        # Limpiar barras existentes
        for widget in self._frame_barras_proveedores.winfo_children():
            widget.destroy()

        # Contar por proveedor
        conteo: Dict[str, int] = {}
        for r in self._resultados:
            proveedor = r.get("proveedor")
            if proveedor:
                conteo[proveedor.lower()] = conteo.get(proveedor.lower(), 0) + 1

        total_con_precio = sum(conteo.values())
        if total_con_precio == 0:
            return

        # Crear barras proporcionales
        for proveedor, cantidad in conteo.items():
            proporcion = cantidad / total_con_precio
            color = self.COLORES_PROVEEDORES.get(proveedor, self.tema["acento"])

            barra = ctk.CTkFrame(
                self._frame_barras_proveedores,
                fg_color=color,
                corner_radius=0,
            )
            barra.place(
                relwidth=proporcion,
                relheight=1.0,
                relx=sum(
                    conteo.get(p, 0) / total_con_precio
                    for p in list(conteo.keys())[: list(conteo.keys()).index(proveedor)]
                ),
            )

    def _exportar_excel(self) -> None:
        """Exporta los resultados a un archivo Excel."""
        if not self._resultados:
            messagebox.showinfo("Sin datos", "No hay resultados para exportar.")
            return

        # Pedir ubicación del archivo
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"resultados_hoteles_{fecha}.xlsx",
        )

        if not filename:
            return

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill

            wb = Workbook()
            ws = wb.active
            ws.title = "Resultados"

            # Encabezados
            headers = [
                "#",
                "Hotel",
                "Precio",
                "Moneda",
                "Proveedor",
                "Check-in",
                "Check-out",
            ]
            header_font = Font(bold=True)
            header_fill = PatternFill(
                start_color="366092", end_color="366092", fill_type="solid"
            )

            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")

            # Datos
            for idx, resultado in enumerate(self._resultados_filtrados, 2):
                ws.cell(row=idx, column=1, value=idx - 1)
                ws.cell(row=idx, column=2, value=resultado.get("hotel", ""))
                ws.cell(row=idx, column=3, value=resultado.get("precio"))
                ws.cell(row=idx, column=4, value=resultado.get("moneda", ""))
                ws.cell(row=idx, column=5, value=resultado.get("proveedor", ""))
                ws.cell(row=idx, column=6, value=resultado.get("check_in", ""))
                ws.cell(row=idx, column=7, value=resultado.get("check_out", ""))

            # Ajustar anchos
            ws.column_dimensions["A"].width = 5
            ws.column_dimensions["B"].width = 40
            ws.column_dimensions["C"].width = 12
            ws.column_dimensions["D"].width = 10
            ws.column_dimensions["E"].width = 12
            ws.column_dimensions["F"].width = 12
            ws.column_dimensions["G"].width = 12

            wb.save(filename)
            messagebox.showinfo("Exportado", f"Resultados exportados a:\n{filename}")

        except ImportError:
            messagebox.showerror(
                "Error", "openpyxl no está instalado. Ejecute: pip install openpyxl"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    def _copiar_portapapeles(self) -> None:
        """Copia los resultados al portapapeles."""
        if not self._resultados_filtrados:
            messagebox.showinfo("Sin datos", "No hay resultados para copiar.")
            return

        lineas = ["Hotel\tPrecio\tMoneda\tProveedor\tCheck-in\tCheck-out"]

        for r in self._resultados_filtrados:
            precio = f"${r.get('precio'):.2f}" if r.get("precio") else "-"
            linea = (
                f"{r.get('hotel', '')}\t{precio}\t{r.get('moneda', '-')}\t"
                f"{r.get('proveedor', '-')}\t{r.get('check_in', '-')}\t{r.get('check_out', '-')}"
            )
            lineas.append(linea)

        texto = "\n".join(lineas)

        self.clipboard_clear()
        self.clipboard_append(texto)

        messagebox.showinfo(
            "Copiado",
            f"{len(self._resultados_filtrados)} resultados copiados al portapapeles.",
        )

    def cambiar_tema(self, modo_tema: TemaMode) -> None:
        """Cambia el tema de la pestaña."""
        self.modo_tema = modo_tema
        self.tema = obtener_tema(modo_tema)

        self.frame_resumen.configure(fg_color=self.tema["fondo_secundario"])
        self.frame_filtros.configure(fg_color=self.tema["fondo_secundario"])
        self.frame_tabla.configure(fg_color=self.tema["fondo_secundario"])

    def limpiar_resultados(self) -> None:
        """Limpia todos los resultados."""
        self._resultados = []
        self._resultados_filtrados = []
        self._actualizar_tabla()
        self._actualizar_metricas()

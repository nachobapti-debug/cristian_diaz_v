import math
import random
import tkinter as tk
from collections import Counter
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk

import mysql.connector
from mysql.connector import Error


CONFIGURACION_MYSQL = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "database": "AgenciaVehiculosDB",
}

# Las tuplas representan opciones fijas que no deben cambiar durante la ejecución.
COMBUSTIBLES = ("Gasolina", "Diésel", "Híbrido", "Eléctrico")
ESTADOS_MANTENIMIENTO = ("Operativo", "En mantenimiento", "Fuera de servicio")


class AplicacionVehiculos:
    def __init__(self, ventana, conexion):
        self.ventana = ventana
        self.conexion = conexion
        self.id_seleccionado = None

        self.ventana.title("Gestión de Vehículos - Agencia de Alquiler")
        self.ventana.geometry("1180x700")
        self.ventana.minsize(1020, 620)
        self.ventana.configure(bg="#eef2f4")

        self.configurar_estilos()
        self.crear_interfaz()
        self.mostrar_vehiculos()

    def configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Treeview",
            rowheight=28,
            font=("Calibri", 10),
            background="#ffffff",
            fieldbackground="#ffffff",
        )
        estilo.configure(
            "Treeview.Heading",
            font=("Calibri", 10, "bold"),
            background="#dce7e3",
            foreground="#183f36",
        )
        estilo.configure(
            "Accion.TButton",
            font=("Calibri", 10, "bold"),
            padding=(12, 8),
        )

    def crear_interfaz(self):
        encabezado = tk.Frame(self.ventana, bg="#173f36", height=82)
        encabezado.pack(fill="x")
        encabezado.pack_propagate(False)

        tk.Label(
            encabezado,
            text="Gestión de Vehículos",
            bg="#173f36",
            fg="white",
            font=("Calibri", 21, "bold"),
        ).pack(anchor="w", padx=28, pady=(14, 0))

        tk.Label(
            encabezado,
            text="Agencia de alquiler - inventario, disponibilidad y mantenimiento",
            bg="#173f36",
            fg="#dbeae5",
            font=("Calibri", 10),
        ).pack(anchor="w", padx=29)

        contenido = tk.Frame(self.ventana, bg="#eef2f4")
        contenido.pack(fill="both", expand=True, padx=22, pady=18)
        contenido.columnconfigure(1, weight=1)
        contenido.rowconfigure(0, weight=1)

        formulario = tk.LabelFrame(
            contenido,
            text=" Datos del vehículo ",
            bg="#ffffff",
            fg="#173f36",
            font=("Calibri", 11, "bold"),
            padx=18,
            pady=15,
        )
        formulario.grid(row=0, column=0, sticky="ns", padx=(0, 16))

        self.entrada_marca = self.crear_campo(formulario, "Marca:", 0)
        self.entrada_modelo = self.crear_campo(formulario, "Modelo:", 1)
        self.entrada_anio = self.crear_campo(formulario, "Año:", 2)

        tk.Label(
            formulario,
            text="Combustible:",
            bg="#ffffff",
            fg="#263746",
            font=("Calibri", 10),
        ).grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.combo_combustible = ttk.Combobox(
            formulario,
            values=COMBUSTIBLES,
            state="readonly",
            width=26,
            font=("Calibri", 10),
        )
        self.combo_combustible.grid(
            row=3, column=1, sticky="ew", padx=(12, 0), pady=(0, 12)
        )
        self.combo_combustible.set(COMBUSTIBLES[0])

        tk.Label(
            formulario,
            text="Mantenimiento:",
            bg="#ffffff",
            fg="#263746",
            font=("Calibri", 10),
        ).grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.combo_mantenimiento = ttk.Combobox(
            formulario,
            values=ESTADOS_MANTENIMIENTO,
            state="readonly",
            width=26,
            font=("Calibri", 10),
        )
        self.combo_mantenimiento.grid(
            row=4, column=1, sticky="ew", padx=(12, 0), pady=(0, 12)
        )
        self.combo_mantenimiento.set(ESTADOS_MANTENIMIENTO[0])

        self.entrada_tarifa = self.crear_campo(
            formulario, "Tarifa diaria ($):", 5
        )

        self.var_disponible = tk.BooleanVar(value=True)
        tk.Checkbutton(
            formulario,
            text="Disponible para alquilar",
            variable=self.var_disponible,
            bg="#ffffff",
            activebackground="#ffffff",
            fg="#263746",
            font=("Calibri", 10),
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(2, 12))

        botones = tk.Frame(formulario, bg="#ffffff")
        botones.grid(row=7, column=0, columnspan=2, pady=(12, 0))
        for columna in range(2):
            botones.columnconfigure(columna, weight=1)

        ttk.Button(
            botones,
            text="Agregar",
            command=self.agregar_vehiculo,
            style="Accion.TButton",
        ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(
            botones,
            text="Actualizar",
            command=self.actualizar_vehiculo,
            style="Accion.TButton",
        ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(
            botones,
            text="Eliminar",
            command=self.eliminar_vehiculo,
            style="Accion.TButton",
        ).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(
            botones,
            text="Limpiar",
            command=self.limpiar_formulario,
            style="Accion.TButton",
        ).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(
            botones,
            text="Generar informe",
            command=self.generar_informe,
            style="Accion.TButton",
        ).grid(row=2, column=0, columnspan=2, padx=4, pady=(12, 4), sticky="ew")

        listado = tk.LabelFrame(
            contenido,
            text=" Vehículos registrados ",
            bg="#ffffff",
            fg="#173f36",
            font=("Calibri", 11, "bold"),
            padx=12,
            pady=12,
        )
        listado.grid(row=0, column=1, sticky="nsew")
        listado.columnconfigure(0, weight=1)
        listado.rowconfigure(0, weight=1)

        columnas = (
            "ID",
            "Marca",
            "Modelo",
            "Anio",
            "Combustible",
            "Disponible",
            "Mantenimiento",
            "Tarifa",
        )
        self.tabla = ttk.Treeview(
            listado,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )

        encabezados = {
            "ID": "ID",
            "Marca": "Marca",
            "Modelo": "Modelo",
            "Anio": "Año",
            "Combustible": "Combustible",
            "Disponible": "Disponible",
            "Mantenimiento": "Mantenimiento",
            "Tarifa": "Tarifa diaria",
        }
        anchos = {
            "ID": 48,
            "Marca": 90,
            "Modelo": 105,
            "Anio": 60,
            "Combustible": 90,
            "Disponible": 80,
            "Mantenimiento": 125,
            "Tarifa": 95,
        }

        for columna in columnas:
            self.tabla.heading(columna, text=encabezados[columna])
            self.tabla.column(
                columna,
                width=anchos[columna],
                minwidth=anchos[columna],
                anchor="center" if columna in {"ID", "Anio", "Disponible"} else "w",
            )

        barra_vertical = ttk.Scrollbar(
            listado, orient="vertical", command=self.tabla.yview
        )
        barra_horizontal = ttk.Scrollbar(
            listado, orient="horizontal", command=self.tabla.xview
        )
        self.tabla.configure(
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set,
        )
        self.tabla.grid(row=0, column=0, sticky="nsew")
        barra_vertical.grid(row=0, column=1, sticky="ns")
        barra_horizontal.grid(row=1, column=0, sticky="ew")
        self.tabla.bind("<<TreeviewSelect>>", self.cargar_seleccion)

        pie = tk.Frame(self.ventana, bg="#dce7e3", height=34)
        pie.pack(fill="x", side="bottom")
        pie.pack_propagate(False)
        self.estado = tk.Label(
            pie,
            text="Conexión establecida con AgenciaVehiculosDB",
            bg="#dce7e3",
            fg="#284e45",
            font=("Calibri", 9),
        )
        self.estado.pack(anchor="w", padx=24, pady=7)

    def crear_campo(self, contenedor, etiqueta, fila):
        tk.Label(
            contenedor,
            text=etiqueta,
            bg="#ffffff",
            fg="#263746",
            font=("Calibri", 10),
        ).grid(row=fila, column=0, sticky="w", pady=(0, 5))

        entrada = ttk.Entry(contenedor, width=29, font=("Calibri", 10))
        entrada.grid(row=fila, column=1, sticky="ew", padx=(12, 0), pady=(0, 12))
        return entrada

    def obtener_datos_formulario(self):
        marca = self.entrada_marca.get().strip().title()
        modelo = self.entrada_modelo.get().strip().title()
        combustible = self.combo_combustible.get()
        mantenimiento = self.combo_mantenimiento.get()
        texto_anio = self.entrada_anio.get().strip()
        texto_tarifa = self.entrada_tarifa.get().strip()

        if not marca or not modelo or not texto_anio or not texto_tarifa:
            raise ValueError("Debe completar todos los campos del formulario.")

        try:
            anio = int(texto_anio)
        except ValueError as error:
            raise ValueError("El año debe ser un número entero.") from error

        anio_actual = datetime.now().year
        if anio < 1950 or anio > anio_actual + 1:
            raise ValueError(f"El año debe estar entre 1950 y {anio_actual + 1}.")

        try:
            tarifa = float(texto_tarifa.replace(",", "."))
        except ValueError as error:
            raise ValueError("La tarifa debe ser un número válido.") from error

        if not math.isfinite(tarifa) or tarifa <= 0:
            raise ValueError("La tarifa debe ser mayor que cero.")

        disponible = bool(self.var_disponible.get())
        if mantenimiento != "Operativo":
            disponible = False

        return (
            marca,
            modelo,
            anio,
            combustible,
            disponible,
            mantenimiento,
            round(tarifa, 2),
        )

    def agregar_vehiculo(self):
        try:
            datos = self.obtener_datos_formulario()
            consulta = """
                INSERT INTO Vehiculos
                    (Marca, Modelo, Anio, Combustible, Disponible,
                     EstadoMantenimiento, TarifaAlquiler)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor = self.conexion.cursor()
            cursor.execute(consulta, datos)
            self.conexion.commit()
            nuevo_id = cursor.lastrowid
            cursor.close()

            self.mostrar_vehiculos()
            self.limpiar_formulario()
            self.actualizar_estado(f"Vehículo ID {nuevo_id} agregado correctamente.")
            messagebox.showinfo("Registro exitoso", "El vehículo fue agregado.")
        except ValueError as error:
            messagebox.showwarning("Datos inválidos", str(error))
        except Error as error:
            self.conexion.rollback()
            messagebox.showerror("Error de base de datos", str(error))

    def mostrar_vehiculos(self):
        try:
            consulta = """
                SELECT ID, Marca, Modelo, Anio, Combustible, Disponible,
                       EstadoMantenimiento, TarifaAlquiler
                FROM Vehiculos
                ORDER BY ID
            """
            cursor = self.conexion.cursor(dictionary=True)
            cursor.execute(consulta)
            vehiculos = cursor.fetchall()
            cursor.close()

            for elemento in self.tabla.get_children():
                self.tabla.delete(elemento)

            for vehiculo in vehiculos:
                disponibilidad = "Sí" if vehiculo["Disponible"] else "No"
                tarifa = f"${float(vehiculo['TarifaAlquiler']):,.0f}"
                self.tabla.insert(
                    "",
                    tk.END,
                    values=(
                        vehiculo["ID"],
                        vehiculo["Marca"],
                        vehiculo["Modelo"],
                        vehiculo["Anio"],
                        vehiculo["Combustible"],
                        disponibilidad,
                        vehiculo["EstadoMantenimiento"],
                        tarifa,
                    ),
                )

            self.actualizar_estado(
                f"Se muestran {len(vehiculos)} vehículo(s) registrado(s)."
            )
        except Error as error:
            messagebox.showerror("Error de consulta", str(error))

    def actualizar_vehiculo(self):
        if self.id_seleccionado is None:
            messagebox.showwarning(
                "Seleccione un vehículo",
                "Seleccione un registro de la tabla antes de actualizar.",
            )
            return

        try:
            datos = self.obtener_datos_formulario()
            consulta = """
                UPDATE Vehiculos
                SET Marca = %s,
                    Modelo = %s,
                    Anio = %s,
                    Combustible = %s,
                    Disponible = %s,
                    EstadoMantenimiento = %s,
                    TarifaAlquiler = %s
                WHERE ID = %s
            """
            parametros = datos + (self.id_seleccionado,)
            cursor = self.conexion.cursor()
            cursor.execute(consulta, parametros)
            self.conexion.commit()
            cursor.close()

            identificador = self.id_seleccionado
            self.mostrar_vehiculos()
            self.limpiar_formulario()
            self.actualizar_estado(
                f"Vehículo ID {identificador} actualizado correctamente."
            )
            messagebox.showinfo("Actualización exitosa", "El vehículo fue actualizado.")
        except ValueError as error:
            messagebox.showwarning("Datos inválidos", str(error))
        except Error as error:
            self.conexion.rollback()
            messagebox.showerror("Error de base de datos", str(error))

    def eliminar_vehiculo(self):
        if self.id_seleccionado is None:
            messagebox.showwarning(
                "Seleccione un vehículo",
                "Seleccione un registro de la tabla antes de eliminar.",
            )
            return

        confirmacion = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Desea eliminar el vehículo ID {self.id_seleccionado}?",
        )
        if not confirmacion:
            return

        try:
            identificador = self.id_seleccionado
            cursor = self.conexion.cursor()
            cursor.execute("DELETE FROM Vehiculos WHERE ID = %s", (identificador,))
            self.conexion.commit()
            cursor.close()

            self.mostrar_vehiculos()
            self.limpiar_formulario()
            self.actualizar_estado(
                f"Vehículo ID {identificador} eliminado correctamente."
            )
            messagebox.showinfo("Eliminación exitosa", "El vehículo fue eliminado.")
        except Error as error:
            self.conexion.rollback()
            messagebox.showerror("Error de base de datos", str(error))

    def generar_informe(self):
        try:
            cursor = self.conexion.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT ID, Marca, Modelo, Anio, Combustible, Disponible,
                       EstadoMantenimiento, TarifaAlquiler
                FROM Vehiculos
                ORDER BY ID
                """
            )
            vehiculos = cursor.fetchall()
            cursor.close()
        except Error as error:
            messagebox.showerror("Error de consulta", str(error))
            return

        if not vehiculos:
            messagebox.showinfo("Sin información", "No existen vehículos registrados.")
            return

        # La consulta se recibe como una lista de diccionarios.
        conteo_disponibilidad = Counter(
            "Disponible" if vehiculo["Disponible"] else "No disponible"
            for vehiculo in vehiculos
        )
        conteo_combustibles = Counter(
            vehiculo["Combustible"] for vehiculo in vehiculos
        )
        combustibles_unicos = {
            vehiculo["Combustible"] for vehiculo in vehiculos
        }

        tarifas = [float(vehiculo["TarifaAlquiler"]) for vehiculo in vehiculos]
        promedio_tarifa = math.ceil(sum(tarifas) / len(tarifas))
        folio = f"INF-{datetime.now():%Y%m%d}-{random.randint(1000, 9999)}"

        lineas = [
            "INFORME DE FLOTA",
            f"Folio: {folio}",
            f"Fecha y hora: {datetime.now():%d-%m-%Y %H:%M}",
            "",
            f"Total de vehículos: {len(vehiculos)}",
            f"Disponibles: {conteo_disponibilidad['Disponible']}",
            f"No disponibles: {conteo_disponibilidad['No disponible']}",
            f"Tarifa diaria promedio aproximada: ${promedio_tarifa:,.0f}",
            f"Combustibles presentes: {', '.join(sorted(combustibles_unicos))}",
            "",
            "Distribución por combustible:",
        ]

        for combustible, cantidad in sorted(conteo_combustibles.items()):
            lineas.append(f"- {combustible}: {cantidad}")

        lineas.extend(["", "Vehículos no disponibles o en mantenimiento:"])
        vehiculos_observados = [
            vehiculo
            for vehiculo in vehiculos
            if not vehiculo["Disponible"]
            or vehiculo["EstadoMantenimiento"] != "Operativo"
        ]

        if vehiculos_observados:
            for vehiculo in vehiculos_observados:
                lineas.append(
                    f"- ID {vehiculo['ID']}: {vehiculo['Marca']} "
                    f"{vehiculo['Modelo']} - {vehiculo['EstadoMantenimiento']}"
                )
        else:
            lineas.append("- No existen vehículos con observaciones.")

        ventana_informe = tk.Toplevel(self.ventana)
        ventana_informe.title(f"Informe de flota - {folio}")
        ventana_informe.geometry("650x520")
        ventana_informe.transient(self.ventana)

        texto = tk.Text(
            ventana_informe,
            wrap="word",
            font=("Consolas", 10),
            padx=18,
            pady=16,
        )
        texto.pack(fill="both", expand=True)
        texto.insert("1.0", "\n".join(lineas))
        texto.configure(state="disabled")

        self.actualizar_estado(f"Informe {folio} generado correctamente.")

    def cargar_seleccion(self, _evento):
        seleccion = self.tabla.selection()
        if not seleccion:
            return

        valores = self.tabla.item(seleccion[0], "values")
        self.id_seleccionado = int(valores[0])

        try:
            cursor = self.conexion.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT ID, Marca, Modelo, Anio, Combustible, Disponible,
                       EstadoMantenimiento, TarifaAlquiler
                FROM Vehiculos
                WHERE ID = %s
                """,
                (self.id_seleccionado,),
            )
            vehiculo = cursor.fetchone()
            cursor.close()
        except Error as error:
            messagebox.showerror("Error de consulta", str(error))
            return

        if vehiculo is None:
            return

        self.limpiar_formulario(conservar_seleccion=True)
        self.entrada_marca.insert(0, vehiculo["Marca"])
        self.entrada_modelo.insert(0, vehiculo["Modelo"])
        self.entrada_anio.insert(0, vehiculo["Anio"])
        self.combo_combustible.set(vehiculo["Combustible"])
        self.combo_mantenimiento.set(vehiculo["EstadoMantenimiento"])
        self.entrada_tarifa.insert(0, float(vehiculo["TarifaAlquiler"]))
        self.var_disponible.set(bool(vehiculo["Disponible"]))
        self.actualizar_estado(f"Vehículo ID {self.id_seleccionado} seleccionado.")

    def limpiar_formulario(self, conservar_seleccion=False):
        for entrada in (
            self.entrada_marca,
            self.entrada_modelo,
            self.entrada_anio,
            self.entrada_tarifa,
        ):
            entrada.delete(0, tk.END)

        self.combo_combustible.set(COMBUSTIBLES[0])
        self.combo_mantenimiento.set(ESTADOS_MANTENIMIENTO[0])
        self.var_disponible.set(True)

        if not conservar_seleccion:
            self.id_seleccionado = None
            for elemento in self.tabla.selection():
                self.tabla.selection_remove(elemento)

    def actualizar_estado(self, mensaje):
        self.estado.config(text=mensaje)

    def cerrar_aplicacion(self):
        if self.conexion.is_connected():
            self.conexion.close()
        self.ventana.destroy()


def iniciar_aplicacion():
    ventana = tk.Tk()
    ventana.withdraw()

    contrasena = simpledialog.askstring(
        "Conexión a MySQL",
        "Ingrese la contraseña del usuario root:",
        show="*",
        parent=ventana,
    )

    if contrasena is None:
        ventana.destroy()
        return

    try:
        conexion = mysql.connector.connect(
            **CONFIGURACION_MYSQL,
            password=contrasena,
        )
    except Error as error:
        messagebox.showerror(
            "No fue posible conectar",
            "Revise que MySQL esté activo, que la base de datos exista "
            f"y que la contraseña sea correcta.\n\nDetalle: {error}",
            parent=ventana,
        )
        ventana.destroy()
        return

    ventana.deiconify()
    aplicacion = AplicacionVehiculos(ventana, conexion)
    ventana.protocol("WM_DELETE_WINDOW", aplicacion.cerrar_aplicacion)
    ventana.mainloop()


if __name__ == "__main__":
    iniciar_aplicacion()

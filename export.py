import argparse
import pandas as pd
from DatabaseManager import DatabaseManager


def export_database_to_excel(database_name, table_name, output_file):
    """
    Exporta una tabla de la base de datos especificada a un archivo Excel.

    Args:
        database_name (str): Nombre de la base de datos configurada
        table_name (str): Nombre de la tabla a exportar
        output_file (str): Ruta del archivo Excel de salida
    """
    db_manager = None
    try:
        # Conectar a la base de datos CORRECTO (usando parámetro)
        db_manager = DatabaseManager(database_name)
        db_manager.connect()

        # Obtener datos de la tabla CORRECTO (usando parámetro y sintaxis válida)
        query = f'SELECT * FROM "{table_name}";'
        result = db_manager.execute_query(query)

        # Convertir a DataFrame de pandas
        df = pd.DataFrame(result)

        # Guardar en Excel
        df.to_excel(output_file, index=False)
        print(f"Datos exportados exitosamente a {output_file}")

    except Exception as e:
        print(f"Error al exportar datos: {str(e)}")
        raise
    finally:
        if db_manager:
            db_manager.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Exportar datos de PostgreSQL a Excel')
    parser.add_argument('--database', required=True,
                        help='Nombre de la base de datos (ej. Personal, Producción)')
    parser.add_argument('--table', required=True,
                        help='Nombre de la tabla a exportar')
    parser.add_argument('--output', default='output.xlsx',
                        help='Nombre del archivo Excel de salida (default: output.xlsx)')

    args = parser.parse_args()

    export_database_to_excel(
        database_name=args.database,
        table_name=args.table,
        output_file=args.output
    )

import sqlite3


class qcodes_database_manager:
    def __init__(self, database_name):
        self.database_name = database_name

    experiment_id = 0

    def delete_run_id(self, run_id):
        conn = sqlite3.connect(self.database_name)
        cursor = conn.cursor()

        sql_delete_query = "DELETE from layouts where run_id = " + str(int(run_id))
        cursor.execute(sql_delete_query)

        conn.commit()
        conn.close()

    def delete_run_id_list(self, run_id_list):
        conn = sqlite3.connect(self.database_name)
        cursor = conn.cursor()

        for run_id in run_id_list:
            sql_delete_query = (
                "DELETE from [results" + "--" + str(int(run_id)) + "] where id = 1"
            )
            # sql_delete_query = 'DROP TABLE [results-'+str(int(self.experiment_id))+'-'+str(int(run_id))+']'
            print(sql_delete_query)
            cursor.execute(sql_delete_query)

        conn.commit()
        conn.close()

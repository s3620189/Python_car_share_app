import os
import click
from flask import Flask
from flask import current_app
from flask.cli import with_appcontext
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor

mysql = MySQL(cursorclass=DictCursor)


def readSqlStmts(sqlfile):
    '''Read SQL statements from files

    Args:
        A file containing multiple SQL statements

    Returns:
        (list) SQL statements
    '''

    sqlstmts = []
    sqlstmt = None
    with current_app.open_resource(sqlfile) as f:
        while True:
            line = f.readline().decode("utf8")
            if not line:
                break

            line = line.strip()
            if len(line) == 0:
                continue

            if sqlstmt is None:
                sqlstmt = line
            else:
                sqlstmt += " " + line

            if line[-1] == ";":
                sqlstmts.append(sqlstmt)
                sqlstmt = None

    return sqlstmts


@click.command("init-db")
@with_appcontext
def initDb():
    '''Text-mode command to initialise database

    (shell)$ flask init-db
    '''

    click.echo("Initialising db...")

    try:
        db = mysql.get_db()
        cursor = db.cursor()

        # database schema
        schema_sql = os.path.join(
            os.path.dirname(__file__), "sql", "schema.sql")
        sqlstmts = readSqlStmts(schema_sql)
        # cars
        data_sql = os.path.join(os.path.dirname(__file__), "sql", "data.sql")
        sqlstmts.extend(readSqlStmts(data_sql))
        for sqlstmt in sqlstmts:
            cursor.execute(sqlstmt)

        db.commit()
        cursor.close()
    except Exception as e:
        click.echo("Error: %s" % (e,))

    click.echo("Done.")


def create_app(test_config=None):
    '''Entry point of Flask application

    Server-side configurations are also specified here.

    Returns:
        (Flask) Flask application
    '''

    app = Flask(__name__)
    # GCP MySQL details
    app.config["MYSQL_DATABASE_HOST"] = "34.87.252.199"
    app.config["MYSQL_DATABASE_USER"] = "root"
    app.config["MYSQL_DATABASE_PASSWORD"] = "123"
    app.config["MYSQL_DATABASE_DB"] = "DB"
    # secret key for web session
    app.config["SECRET_KEY"] = "df66db2e684e8b0c814d0ba10ef7235a"

    unit_test_db = os.environ.get("UNIT_TEST_DB")
    if unit_test_db is not None:
        app.config["MYSQL_DATABASE_DB"] = unit_test_db

    if test_config is not None:
        app.config.update(test_config)

    mysql.init_app(app)

    app.cli.add_command(initDb)

    from . import api
    # URI prefix for RESTful API
    app.register_blueprint(api.bp, url_prefix="/api")

    from . import web
    app.register_blueprint(web.bp)

    return app

from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, send_file
from io import BytesIO
import openpyxl
from flask_mysqldb import MySQL, MySQLdb
import bcrypt

#from datetime import datetime
app = Flask(__name__)
#MySQL Connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'pako'
app.config['MYSQL_PASSWORD'] = 'Fierro123'
app.config['MYSQL_DB'] = 'flaskcontacts'
mysql = MySQL(app)
#Settings
app.secret_key = 'mysecretkey'
encriptar = bcrypt.gensalt()

@app.route('/')
def main():
    if 'nombre' in session:
        return render_template('index.html')
    else:
        return render_template('login.html')

#Index
@app.route('/index')
def Index():
    if 'nombre' in session:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM contacts')
        data = cur.fetchall()
        return render_template('index.html', contacts = data)
    else:
        return render_template('login.html')

#Login        
@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        passwd = request.form['passwd'].encode('utf-8')

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE username=%s",(username,))
        user = cur.fetchone()
        cur.close()

        if user:
            if bcrypt.hashpw(passwd, user['passwd'].encode('utf-8')) == user['passwd'].encode('utf-8'):
                session['loggedin'] = True
                session['idUser'] = user['idUser']
                session['nombre'] = user['nombre']
                session['username'] = user['username']
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM contacts')
                data = cur.fetchall()
                flash('¡Inicio de sesión exitoso!')
                return redirect(url_for('Index', contact = data))
                #return render_template('index.html', contact = data)
            else:
                 flash('ACCESO DENEGADO', 'altert-danger')
                 return render_template('login.html')
        else:
             flash('ACCESO DENEGADO', 'altert-danger')
             return render_template('login.html') 
    else:
        flash('ACCESO DENEGADO', 'altert-danger')
        return render_template('login.html') 





#Register
@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        nombre = request.form['nombre']
        username = request.form['username']
        passwd = request.form['passwd'].encode('utf-8')
        hash_password = bcrypt.hashpw(passwd, bcrypt.gensalt())
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO users (nombre, username, passwd) VALUES(%s, %s, %s)',(nombre,username,hash_password,))
        mysql.connection.commit()
        flash('You are now registered and can log in')
        session['nombre'] = nombre
        session['username'] = username
        return redirect(url_for('login'))



#Logout
@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')



@app.route('/add_contact', methods=['POST'])
def add_Contact():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        email = request.form['email']
        planInscripcion = request.form['planInscripcion']
        fechaIngreso = request.form['fechaIngreso']
        fechaVencimiento = request.form['fechaVencimiento']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO contacts (nombre, telefono, email, planInscripcion, fechaIngreso, fechaVencimiento) VALUES (%s, %s, %s, %s, %s, %s)", (nombre, telefono, email, planInscripcion, fechaIngreso, fechaVencimiento))
        mysql.connection.commit()
        flash('El contacto se agrego correctamente!')
        cur.close()
        return redirect(url_for('Index'))
  
@app.route('/edit/<id>')
def get_contact(id):
    cur =  mysql.connection.cursor()
    cur.execute('SELECT * FROM contacts WHERE id = %s', (id))
    data = cur.fetchall()
    return render_template('edit-contact.html', contact = data[0])
    
@app.route('/update/<id>', methods = ['POST'])
def update_contact(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        email = request.form['email']
        planInscripcion = request.form['planInscripcion']
        fechaIngreso = request.form['fechaIngreso']
        fechaVencimiento = request.form['fechaVencimiento']
        cur = mysql.connection.cursor()
        cur.execute("""
        UPDATE contacts
            SET nombre=%s, telefono=%s, email=%s, planInscripcion=%s, fechaIngreso=%s, fechaVencimiento=%s
            WHERE id = %s""", (nombre, telefono, email, planInscripcion, fechaIngreso, fechaVencimiento, id))
        mysql.connection.commit()
        flash('Los datos se actualizaron correctamente!')
        return redirect(url_for('Index'))
    
@app.route('/delete/<string:id>')
def delete_Contact(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM contacts WHERE id={0}'.format(id))
    mysql.connection.commit()
    flash("El contacto se eliminó correctamente!")
    return redirect(url_for('Index'))

@app.route('/asistencia', methods=['GET','POST'])
def asistencia():
    if request.method == 'POST':
        # Obtén el ID del formulario
        id = request.form['id']

        # Consulta a la base de datos para obtener los detalles del usuario
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, nombre, fechaIngreso, fechaVencimiento, planInscripcion FROM contacts WHERE id = %s", (id))
        resultado = cur.fetchone()

        # Renderiza la plantilla con los detalles del resultado
        return render_template('asistencia.html', resultado=resultado)

    # Si es una solicitud GET, simplemente renderiza el formulario
    return render_template('asistencia.html')

@app.route('/exportar_excel')
def exportar_excel():
    # Obtener datos de la base de datos
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM contacts")
    contacts = cur.fetchall()

    # Crear un libro de Excel y una hoja
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    # Añadir encabezados
    headers = ["Id", "Nombre", "Telefono", "Email", "Fecha de Ingreso", "Fecha de Vencimiento", "Plan de Inscripcion"]
    sheet.append(headers)

    # Añadir datos
    for contact in contacts:
        sheet.append(contact)

    # Crear un objeto BytesIO
    output = BytesIO()

    # Guardar el libro de Excel en el objeto BytesIO
    workbook.save(output)

    # Crear una respuesta con el contenido del objeto BytesIO
    response = make_response(output.getvalue())

    # Establecer las cabeceras para indicar que es un archivo de Excel
    response.headers["Content-Disposition"] = "attachment; filename=contactos.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response


if __name__ == '__main__':
    app.run(port = 3000, debug = True)
from flask import Flask, session, request

app = Flask(__name__)

@app.route('/')
def index():
    if 'username' in session:
        return f'Logged in as {session["username"]}'
    return 'You are not logged in'

@app.route('/login', methods=['GET','POST'])

def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form method="post">
            <p><input type=text id=username name=username>
            <p><input type=text id=username name=password>
            <p><input type=submit value=Login>
        </form>
    '''

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/account/')
def account():
    return 'The account page'

@app.route('/analysis')
def discovery():
    return 'The analysis page'

@app.route('/discovery')
def discovery():
    return 'The about page'

@app.route('/predictions')
def predictions():
    return 'The prediction page'

# if __name__ == '__main__':
#     app.run(port=os.getenv('PORT', 8000))
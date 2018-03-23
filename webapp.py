from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
from bson.objectid import ObjectId

import pprint
import os
import json
import pymongo
# from pymongo import MongoClient

app = Flask(__name__)

app.debug = True # Change this to False for production

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)

# Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], # your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],# your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, # request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' # URL for github's OAuth login
)

# use a JSON file to store the past posts.  A global list variable doesn't work when handling multiple requests coming in and being handled on different threads
# Create and set a global variable for the name of your JSON file here.  The file will be created on Heroku, so you don't need to make it in GitHub

# jsonPosts = 'posts.json'
# os.system("echo '[]' >" + json)
# os.environ['OAUTHLIB_INSECURE_TRANSPORT']='1'
    
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html', past_posts=posts_to_html())

@app.route('/posted', methods=['POST'])
def post():
    # This function should add the new post to the
    #   JSON file of posts and then render home.html
    #   and display the posts.
    # Every post should include the
    #   username of the poster and text of the post.

    try:
        username = session['user_data']['login']
        message = request.form['message']

        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds213239.mlab.com:13239/forumapp")
        db = client["forumapp"]
        posts = db["posts"]


#               **OLD JSON CODE**
#       with open('posts.json', 'r+') as jsonPosts:
#            data = json.load(jsonPosts)
#            data.append({'username':username, 'message':message})
#            jsonPosts.seek(0)
#            jsonPosts.truncate(0)
#            json.dump(data, jsonPosts)

        posts.insert_one({'username': username, 'message': message})
        return render_template('home.html', past_posts=posts_to_html())
    except:
        return render_template('home.html', past_posts="ERROR 001: problem adding new post")

def posts_to_html():
    try:
        #       **OLD JSON CODE**
        #with open('posts.json', 'r') as jsonPosts:
        #    data = json.load(jsonPosts)
        
        tableString = '<table id="postsTable" cellpadding="5"> <tr> <th> Username </th> <th> Message </th> </tr>'
        client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds213239.mlab.com:13239/forumapp")
        db = client["forumapp"]
        posts = db["posts"]
        
        for i in posts.find():
            tableString += " <tr> <td>" + i['username'] + ": </td>"
            tableString += " <td>" + i['message'] + "</td>"
            tableString += ' <td> <form action = "/delete" method = "post"> <button type="submit" name="delete" value=' + i.get('_id') + '>Delete</button></form> </td>'
            tableString += ' </tr> '
        tableString += " </table>"
        table = Markup(tableString)
        return table
    except:
        return "ERROR 002: table construction failed"

''' @app.route('/delete', methods=['POST'])
def delete_post():
    client = pymongo.MongoClient("mongodb://test_user:18s9h64735f124g5e68@ds213239.mlab.com:13239/forumapp")
    db = client["forumapp"]
    posts = db["posts"]
    try:
        deleteID = request.form['delete']
        db.posts.remove( {"_id": ObjectId(deleteID)})
        return render_template('home.html', past_posts=posts_to_html())
    except:
        return render_template('home.html', past_posts="ERROR 003: problem deleting post")
  '''  
    
# redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('message.html', message=message)

# the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')
    
if __name__ == '__main__':
    app.run()

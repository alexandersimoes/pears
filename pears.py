# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, redirect, url_for, abort, session, send_from_directory

app = Flask(__name__, template_folder="html")
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

'''Access to static files'''
@app.route('/uploads/<user>/<path:filename>')
def uploaded_file(user, filename):
    photo_dir = os.path.join(app.config['UPLOAD_FOLDER'], user)
    ''' need to use this send_from_directory function so that the proper HTTP
        headers are set and HTML audio API can work properly'''
    return send_from_directory(photo_dir, filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pears/')
def pears2():
    return render_template('pears.html')

@app.route('/pears2/')
def pears():
    return render_template('pears2.html')

@app.route('/toc/')
def toc():
    return render_template('toc.html')

'''

    Run the file!
    
'''
if __name__ == '__main__':
  app.run()
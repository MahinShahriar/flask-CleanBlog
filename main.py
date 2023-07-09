from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import json
from flask_mail import Mail

app = Flask(__name__, template_folder='template')
app.secret_key = "super-secret-key"
mail = Mail(app)

with open("config.json", "r") as j:
  common = json.load(j)["common"]

local_server = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if (local_server):
  app.config['SQLALCHEMY_DATABASE_URI'] = common["local_uri"]
else:
  app.config['SQLALCHEMY_DATABASE_URI'] = common["prod_uri"]

app.config["UPLOAD_FOLDER"]= common["upload_location"]
# configaring app for Mail operation.
app.config.update(
                  MAIL_SERVER = 'smtp.gmail.com',
                  MAIL_PORT = '465',
                  MAIL_USE_SSL = True,
                  MAIL_USERNAME = common['gmail-user'],
                  MAIL_PASSWORD = common['gmail-pass']
                  )
# Database app
db = SQLAlchemy(app)

# Database table for contact form's data 
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40), nullable=False)
    email= db.Column(db.String(50), nullable=False)
    phone= db.Column(db.String(15))
    msg  = db.Column(db.String(500))

# Database table for posts. 
class Post(db.Model):
    sno = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable=False)
    tagline = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(2000), nullable=False)
    img_file = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(40), nullable=False)

#========HOME  SECTION=======
@app.route('/')
def home():
  posts = Post.query.filter_by().all()
  n = (len(posts)/int(common["num_of_post"]))
  num_of_pages = int(n) if int(n)==n else int(n)+1
  page = request.args.get('page')
  if not str(page).isnumeric():
    page = 1
  page = int(page)
  #  post in page - 3, 12
  posts = posts[(page-1)*int(common["num_of_post"]):page*int(common["num_of_post"])]
  
  if  page==1:
    prev_href = "#"
    next_href = "/?page=" + str(page+1) if num_of_pages!=1 else '#'
  elif page>1 and page<num_of_pages:
    prev_href = "/?page=" + str(page-1)
    next_href = "/?page=" + str(page+1)
  else:
    prev_href = "/?page=" + str(page-1)
    next_href = "#"
  
  return render_template('index.html',common=common,posts=posts, page=page, num=num_of_pages, prev=prev_href, next=next_href)

#========ADMIN  SECTION=======
@app.route('/admin' , methods=['GET','POST'])
def Admin():
  if 'user' in session and session['user']==common['admin_user']:
    posts = Post.query.all()
    return render_template("admin.html", common=common, posts=posts)
  if request.method == "POST":
    uname = request.form.get('uname')
    password = request.form.get('password')
    if (uname==common['admin_user']) and (password==common['admin_password']):
      flash("Login Successfully. Now, you can control admin panel.",'success')
      session['user'] = uname
      posts = Post.query.all()
      return render_template("admin.html", common=common, posts=posts )
    else:
      flash("Username and password not matched. Please try again !",'danger')
  
  return render_template("login.html",common=common)

#========ADMIN LOGOUT SECTION=======
@app.route('/logout')
def logout():
  session.pop('user')
  return redirect("/admin")
  
#========ADMIN/ FILE UPLOADER SECTION=======
@app.route('/uploader' , methods=['GET','POST'])
def Uploader():
  if 'user' in session and session['user']==common['admin_user']:
    if request.method == "POST":
      try:
        f = request.files["file"]
        f.save(os.path.join((app.config['UPLOAD_FOLDER']), secure_filename(f.filename)))
        return redirect('/admin'), flash('File Uploaded Successfully !',"success")
      except :
        return redirect("/admin"), flash('Something went wrong. File upload request denied. Please Try again  !','danger')
#========ADMIN/ Edit  SECTION=======
@app.route('/edit/<string:sno>' , methods=['GET','POST'])
def Edit(sno):
  if ('user' in session) and (session['user']== common['admin_user']):
    if (request.method=="POST"):  
      title = request.form.get('title')
      tagline = request.form.get('tagline')
      slug = request.form.get('slug')
      content = request.form.get('content')
      img_file = request.form.get('img_file')
      if sno=='new':
        new = Post(title=title, tagline=tagline, slug=slug, content=content, img_file=img_file)
        db.session.add(new)
        db.session.commit()
      else:
        post = Post.query.filter_by(sno=sno).first()
        post.title = title
        post.tagline = tagline
        post.slug = slug
        post.content = content
        post.img_file = img_file
        db.session.commit()
        return redirect("/edit/"+sno)
    post = Post.query.filter_by(sno=sno).first()
    return render_template("edit.html", common=common,post=post,sno=sno)

#========ADMIN/ Delete SECTION=======
@app.route('/delete/<string:sno>')
def delete(sno):
  if ('user' in session) and (session['user']== common['admin_user']):
    post = Post.query.filter_by(sno=sno).first()
    db.session.delete(post)
    db.session.commit()
    return redirect('/admin')

#===========CONTACT SECTION=============
# ROUTE FOR CONTACT PAGE
@app.route('/contact' , methods=["GET",'POST'])
def contact():
  if request.method=="POST":
    # Fetching the user datas from the web page.
    username = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    message = request.form.get('message')
    if username and email and phone and message:
    # database operations
      datas = Contact(name=username, email=email, phone=phone, msg= message)
      db.create_all() # creating mentioned conlums at the table.
      db.session.add(datas) # adding the datas at table.
      db.session.commit()
      flash("Contact Information Successfully Sent.\nThank You !",'success')
    else:
      flash('Required Information not inputted properly. Submit request denied . Please Try again....!', 'danger')
      return redirect('/contact')
    
    # mail.send_message('CleanB  : \n',
    #                     sender=email,
    #                     recipients= [common['gmail-user']],
    #                     body=message+'\n\n'+phone
    #                     )
    
  return render_template('contact.html', common=common) 
   
#=========ABOUT SE CTION=============
@app.route('/about')
def About():       
  return render_template('about.html', common=common)

#===========POST SECTION ============
@app.route('/post/<string:post_slug>' , methods=['GET'])
def post_route(post_slug):
  post = Post.query.filter_by(slug=post_slug).first()
  return render_template('post.html', post=post, common=common)
  


#=========== RUN SECTION ===========
if __name__ == '__main__':
    app.run(debug= True) 
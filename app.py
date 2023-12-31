import logging
from flask import Flask,redirect,render_template,url_for,flash,request,session,g
from flask_cors import CORS
from flask_login import LoginManager,login_required,login_user,logout_user,current_user,UserMixin
from forms import login_form,register_form,items_form,mail_form,chnage_pass,manage_user_form,serach_form,CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from werkzeug.security import check_password_hash,generate_password_hash
from datetime import datetime,timedelta
from functions.functions import gen_order_id
from dotenv import load_dotenv
import os
app = Flask(__name__,template_folder="templates")
load_dotenv()
SECRET_KEY = os.environ.get("secret_key")
user_name = os.environ.get("user_name")
password = os.environ.get("password")


app.config["SECRET_KEY"]=os.environ.get("secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{os.environ.get("user_name")}:{os.environ.get("password")}@{os.environ.get("db_host")}:{os.environ.get("db_port")}/{os.environ.get("db_name")}'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
csrf = CORS(app)
db = SQLAlchemy(app)
migrate = Migrate(app,db)
crsf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view="index"
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))



######### db stuff #####
def get_db_session():
    if 'db_session' not in g:
        g.db_session = db.session
    return g.db_session

@app.teardown_appcontext
def teardown_db_session(exception=None):
    db_session = g.pop('db_session', None)
    if db_session is not None:
        try:
            if exception is None:
                db_session.commit()
            else:
                db_session.rollback()
        finally:
            db_session.close()

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(200),nullable=False)
    user_type = db.Column(db.String(20),nullable=False,default="employee")
    create_date =db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_login =db.Column(db.DateTime,nullable=True)
    first_time = db.Column(db.String(20),nullable=False,default="True")
    revoke_acess=db.Column(db.String(20),nullable=False,default="No")
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    
class Item(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    item_name= db.Column(db.String(200),nullable=False)
    brand_name= db.Column(db.String(200),nullable=True)
    stock = db.Column(db.Integer,nullable=False)
    quantity =db.Column(db.String(100),nullable=False)
    price = db.Column(db.Float,nullable=False)
    date = db.Column(db.Date(),default=datetime.utcnow().date() ,nullable=False)
    expiry = db.Column(db.Date())

class Mails(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(255), nullable=False)  
    subject = db.Column(db.String(200), nullable=False)
    reciver = db.Column(db.String(255), nullable=False)  
    date = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow().date())
    open = db.Column(db.Boolean, nullable=False, default=False)  
    message = db.Column(db.Text, nullable=False)



class Orders(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    order_id = db.Column(db.String(200),nullable=False,unique=True)
    creator_id=db.Column(db.Integer,nullable=False)
    creator_name=db.Column(db.String(200),nullable=False)
    status= db.Column(db.String(200),nullable=False,default='Pending')
    itemss = db.relationship("Items",backref="orders")

class Items(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    item_name = db.Column(db.String(200),nullable=False)
    brand_name = db.Column(db.String(200),nullable=False)
    quantity = db.Column(db.Integer,nullable=False)
    s_order_id = db.Column(db.String(200),nullable=False)
    order_id = db.Column(db.Integer,db.ForeignKey("orders.id"))

@app.route("/register",methods=["GET","POST"])

def register():
    form = register_form()
    user=current_user
    try:
        if form.validate_on_submit():
            user_email = Users.query.filter_by(email=form.email.data.strip()).first()
            if user_email is None:
                password_hash=generate_password_hash("1234567")
                add_user= Users(first_name=form.fname.data,last_name=form.lname.data,full_name=form.fname.data+" "+form.lname.data,user_type=form.user_type.data,email=form.email.data,password=password_hash)
                db.session.add(add_user)
                db.session.commit()
                return redirect(url_for("user_list"))
            else:
                form.fname.data=form.fname.data
                form.lname.data=form.lname.data
                form.email.data=form.email.data
                flash("User Already Exists")
                return redirect(url_for("index"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in register: {e}")
    return render_template("register.html",form=form,user=user)

@app.route("/login",methods=["GET","POST"])
def index():
    form=login_form()
    if form.validate_on_submit():
        try:
            user = Users.query.filter_by(email=form.email.data).first()
            if user:
                if user.revoke_acess=="No":
                    if check_password_hash(user.password,form.password.data):
                        login_user(user,remember=True)
                        session.permanent=True
                        user.last_login = datetime.utcnow()
                        db.session.add(user)
                        db.session.commit()
                        form.email.data=""
                        form.password.data=""
                        return redirect(url_for("home",user=user))
                    else:
                        form.email.data=form.email.data
                        flash("Incorrect Password")
                else:
                    flash("Your Access Has Been Revoked Contact Your Manager")
            else:
                form.email.data=form.email.data
                flash("Incorrect Email")
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"SQLAlchemyError in register: {e}")
            flash('Error: Something Went Wrong', 'error')
        except Exception as e :
            logging.error(f"Error in login: {e}")
    return render_template("login.html",form=form)



@app.route("/",methods=["GET","POST"])
@login_required
def home():
    form = items_form()
    pass_form = chnage_pass()
    user =current_user
    todays_date=datetime.utcnow().date()
    one_month = datetime.utcnow().date() + timedelta(days=30)
    recent = Item.query.filter(Item.date==todays_date).limit(5).all()
    expiry_products = Item.query.filter(db.func.Date(Item.expiry)<=one_month)
    expiry = expiry_products.all()
    try:
        if form.validate_on_submit():
            item = Item.query.filter_by(item_name=form.name.data).first()
            if item is None:
                add_item = Item(item_name=form.name.data,brand_name=form.brand_name.data,price=form.price.data,stock=form.stock.data,quantity=form.quantity.data,expiry=form.expiry.data)
                db.session.add(add_item)
                db.session.commit()
                item = Item.query.filter_by(item_name=form.name.data).first()
                flash(item.item_name + " added ScessFully")
                form.name.data=""
                form.brand_name.data=""
                form.stock.data=""
                form.quantity.data=""
                form.expiry.data=""
                return redirect(url_for("home"))
            else:
                flash("Something went wrong ")
        else:
            form.name.data=form.name.data
            form.brand_name.data=form.brand_name.data
            form.price.data=form.price.data
            form.stock.data=form.stock.data
            form.quantity.data=form.quantity.data
            form.expiry.data=form.expiry.data
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in registration: {e}")
    try:
        if pass_form.validate_on_submit():
            if pass_form.new_password.data==pass_form.confrim_password.data:
                phas = generate_password_hash(pass_form.confrim_password.data)
                user = Users.query.get_or_404(user.id)
                user.password=phas
                user.first_time="False"
                db.session.add(user)
                db.session.commit()
                flash("Password Changed")
                return redirect(url_for("home"))
            else:
                flash("Password Doesn't Match")
                return redirect(url_for("home"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in home: {e}")
    return render_template("home.html",user=user,form=form,recent=recent,expiry=expiry,pass_form=pass_form)


################ USER MANAGEMENT ############################
@app.route("/user/list",methods=['GET','POST'])
@login_required
def user_list():
    form = serach_form()
    user=current_user
    try:
        user_list = Users.query.all()
        if form.validate_on_submit():
            user_list = Users.query.filter(or_(Users.first_name == form.search.data.title().strip(),Users.last_name==form.search.data.title().strip(),Users.full_name==form.search.data.title().strip(),Users.email==form.search.data.lower().strip())).all()
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')      
    except Exception as e:
       logging.error(f"Error in user_list: {e}")
    return render_template("userlist.html",user=user,user_list=user_list,form=form)

@app.route("/revoke/<int:id>",methods=["GET","POSt"])
@login_required
def revoke_access(id):
    user=current_user
    try:
        if user.user_type=="Manager":
            get_user = Users.query.get_or_404(id)
            if get_user.revoke_acess == "No":
                get_user.revoke_acess = "Yes"
                db.session.add(get_user)
                db.session.commit()
                flash("Access Revoked")
            elif get_user.revoke_acess=="Yes":
                get_user.revoke_acess = "No"
                db.session.add(get_user)
                db.session.commit()
                flash("Access Granted")
        return redirect(url_for("user_list"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')  
    except Exception as e:
       logging.error(f"Error in revoke_access: {e}")
    return

@app.route("/delete/user/<int:id>",methods=["GET","POST"])
@login_required
def delete_user(id):
    user=current_user
    try:
        if user.user_type=="Manager":
            get_user=Users.query.get_or_404(id)
            db.session.delete(get_user)
            db.session.commit()
            flash("User Deleted")
        else:
            flash("Something went wrong")
        return redirect(url_for("user_list"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
       logging.error(f"Error in registration: {e}")
    return



@app.route("/user/settings/",methods=['GET','POST'])
@login_required
def user_settings():
    user=current_user
    form = chnage_pass()
    try:
        if form.validate_on_submit():     
            if form.new_password.data==form.confrim_password.data:
                phas = generate_password_hash(form.confrim_password.data)
                user = Users.query.get_or_404(user.id)
                user.password=phas
                user.first_time="False"
                db.session.add(user)
                db.session.commit()
                flash("Password Changed")
                return redirect(url_for("user_settings"))
            else:
                flash("Password Doesn't Match")
                return redirect(url_for("user_settings"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in User Setting route: {e}")
    return render_template("user_settings.html",user=user,form=form)



@app.route("/manage/user/<int:id>",methods=["GET","POST"])
@login_required
def manage_user(id):
    form=manage_user_form()
    user=current_user
    get_user = Users.query.get_or_404(id)
    orders = Orders.query.filter_by(creator_id=id).all()
    form.fname.data=get_user.first_name
    form.lname.data=get_user.last_name
    form.user_type.data=get_user.user_type
    form.email.data=get_user.email
    try:
        password_hash=generate_password_hash(form.password.data)
        if form.validate_on_submit():
            if form.password.data=="":
                get_user.first_name=form.fname.data
                password_hash = generate_password_hash(form.password.data)
                get_user.password=password_hash
            get_user.first_name=form.fname.data
            get_user.last_nmae=form.lname.data
            get_user.email=form.email.data
            get_user.user_type=form.user_type.data
            db.session.add(get_user)
            db.session.commit()
            flash("Changes Saved ")
            return redirect(url_for("user_list"))
        else:
            return redirect(url_for("manage_user",id=id))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')       
    except Exception as e:
        logging.error(f"Error in register: {e}")
    return render_template("manage_user.html",form=form,user=user,get_user=get_user,orders=orders)


############## Mail Stuffffff ###############


@app.route("/mails",methods=['GET','POST'])
@login_required
def mails():
    form = serach_form()
    user= current_user
    try:
        mails = Mails.query.order_by(Mails.id.desc()).all()
        if form.validate_on_submit():
            mails=Mails.query.filter_by(sender=form.search.data.lower().strip()).order_by(Mails.id.desc()).all()
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in register: {e}")
    return render_template("mails.html",mails=mails,user=user,form=form)
    
 
@app.route("/compose",methods=['GET','POST'])
@login_required
def compose():
    user=current_user
    form = mail_form()
    try:
        if form.validate_on_submit():
            recive_email = Users.query.filter_by(email=form.reciver.data).first()
            if recive_email:
                mail = Mails(sender=user.email,subject=form.subject.data,reciver=form.reciver.data,message=form.body.data)
                db.session.add(mail)
                db.session.commit()
                flash("Mail Sent")
                form.reciver.data=""
                form.subject.data=""
                form.body.data=""
                return redirect(url_for("mails"))
            else:
                flash("Wrong Email Address ")
                form.reciver.data=form.reciver.data
                form.subject.data=form.subject.data
                form.body.data = form.body.data
                return redirect(url_for("compose"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in delete: {e}")
    return render_template("compose.html",user=user,form=form)

@app.route("/view/mail/<int:id>",methods=["GET","PSOT"])
def view_mails(id):
    try:
        mail = Mails.query.get_or_404(id)
        mail.open = True
        db.session.add(mail)
        db.session.commit()
        print(mail.open)
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in delete: {e}")
    return render_template("view_mail.html",mail=mail)

@app.route("/delete/mail/<int:id>",methods=["GET","PSOT"])
def delete_mails(id):
    try:
        mail = Mails.query.get_or_404(id)
        db.session.delete(mail)
        db.session.commit()
        flash("Mail Deleted")
        return redirect(url_for("mails"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in delete: {e}")
    return redirect(url_for("mails"))


@app.route("/sent",methods=["GET","POST"])
@login_required
def sent_mails():
    user=current_user
    try:
        mails = Mails.query.filter_by(sender=user.email).order_by(Mails.id.desc()).all()
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in delete: {e}")
    return render_template('sent_mail.html',user=user,mails=mails)

 
##########################################################
@app.route("/products",methods=["GET","POST"])
@login_required
def products():
    form =serach_form()
    user=current_user
    try:
        products = Item.query.all()
        product_type = "Products List"
        if form.validate_on_submit():
            products = Item.query.filter(or_(Item.item_name == form.search.data.title().strip(), Item.brand_name == form.search.data.title().strip())).all()
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in delete: {e}")
    return render_template("proucts.html",user=user,products=products,product_type=product_type,form=form)

@app.route("/expiry",methods=["GET","POST"])
@login_required
def expiry():
    form=serach_form()
    user=current_user
    try:
        one_month = datetime.utcnow().date()+timedelta(days=30)
        expiry_products = Item.query.filter(db.func.Date(Item.expiry)<=one_month)
        products = expiry_products.all()
        product_type = "Expiry List"
        if form.validate_on_submit():
            if form.validate_on_submit():
                products = Item.query.filter(or_(Item.item_name == form.search.data.title().strip(), Item.brand_name == form.search.data.title().strip())).all()
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
       logging.error(f"Error in expiry: {e}")
    return render_template("proucts.html",user=user,products=products,product_type=product_type,form=form)

@app.route("/addstock", methods=["GET", "POST"])
@login_required
def add_stock():
    user = current_user
    form = items_form()
    try:
        if form.validate_on_submit():
            item = Item.query.filter_by(item_name=form.name.data).first()
            if item is None:
                add_item = Item(
                    item_name=form.name.data,
                    brand_name=form.brand_name.data,
                    price=form.price.data,
                    stock=form.stock.data,
                    quantity=form.quantity.data,
                    expiry=form.expiry.data,
                )
                db.session.add(add_item)
                db.session.commit()
                flash(f"{add_item.item_name} added successfully")
                return redirect(url_for("add_stock"))
            else:
                flash("Item already exists")
        form.name.data = ""
        form.brand_name.data = ""
        form.price.data = ""
        form.stock.data = ""
        form.quantity.data = ""
        form.expiry.data = ""
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in add_stock: {e}")

    return render_template("addstocks.html", user=user, form=form)

@app.route("/add/<int:id>",methods=["GET","POST"])
@login_required
def add(id):
    try:
        get_item = Item.query.get_or_404(id)
        get_item.stock = get_item.stock+1
        get_item.date=datetime.utcnow().date()
        db.session.add(get_item)
        db.session.commit()
        flash("Stock Added")
        return redirect(url_for("products"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
       logging.error(f"Error in add: {e}")
    return redirect(url_for("products"))

@app.route("/delete/<int:id>",methods=["GET","POST"])
@login_required
def delete(id):
    try:
        get_item = Item.query.get_or_404(id)
        db.session.delete(get_item)
        db.session.commit()
        flash("Stock Removed")
        return redirect(url_for("products"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in delete: {e}")
    return redirect(url_for("products"))
##############################################

def add_items_orders(order_object,data):
    try:
        for i in range(len(data)):
            order_items = Items(item_name=data[i]["item_name"],brand_name=data[i]['brand_name'],quantity=data[i]['quantity'],s_order_id=order_object.order_id,order_id = order_object.id)
            db.session.add(order_items)
            db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
        logging.error(f"Error in expiry {e}")
    return


@app.route("/oders",methods=["GET","POST"])
@crsf.exempt
@login_required
def create_order():
    user = current_user
    product_data = Item.query.all()
    try:
        if request.method == "POST":
            data= request.get_json("data")
            data = data['data']
            orders = Orders(order_id=gen_order_id(),creator_id=user.id,creator_name=user.full_name)
            db.session.add(orders)
            db.session.commit()
            add_items_orders(orders,data)
            return render_template("create_order.html",user=user,product_data=product_data)
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
    except Exception as e:
        logging.error(f"SQLAlchemyError in register: {e}")
    return render_template("create_order.html",user=user,product_data=product_data)

  
@app.route("/order/list/<int:id>",methods=['GET','POST'])
@login_required
def order_list(id):
    user=current_user
    form = serach_form()
    try:
        if form.validate_on_submit():
            orders = Orders.query.filter(or_(Orders.order_id==form.search.data,Orders.creator_name==form.search.data.title().strip(),Orders.status==form.search.data.title().strip())).all()
            print(orders)
            return render_template("order_list.html",orders=orders,user=user,form=form)
        elif id == 0:
            orders = Orders.query.all()
        else:
            orders = Orders.query.filter_by(creator_id=id)
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
       logging.error(f"Error in expiry: {e}")
    return render_template("order_list.html",orders=orders,user=user,form=form)


@app.route("/view/order/<int:id>",methods=["GET","POST"])
@login_required
def view_order(id):
    user = current_user
    try:
        if user.user_type == "Manager":
            order= Orders.query.get_or_404(id)
            order_item = Items.query.filter_by(order_id=order.id).all()
            return render_template("view_order.html",order_item=order_item,user=user,order=order)
        else:
            flash("Something Went Wrong")
            return redirect(url_for("order_list"))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
       logging.error(f"Error in expiry: {e}")
    return render_template("view_order.html",user=user,order_item=order_item,order=order)
    

@app.route("/delete/order/<int:id>",methods=['GET','POST'])
@login_required
def delete_order(id):
    user = current_user
    try:
        if user.user_type == "Manager":
            order= Orders.query.get_or_404(id)
            db.session.delete(order)
            db.session.commit()
            flash("Order Delete")
            return redirect(url_for("order_list",id=0))
        else:
            flash("Something Went Wrong")
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
       logging.error(f"Error in expiry: {e}")
    return redirect(url_for("order_list",id=id))


@app.route("/order/status/<int:id>",methods=['GET','POST'])
def order_status(id):
    user = current_user
    query_param =request.args.get('query_param',default=None)
    try:
        if user.user_type=='Manager':
            if query_param=='Approved':
                order = Orders.query.get_or_404(id)
                order.status = "Approved"
                db.session.add(order)
                db.session.commit()
                flash('Order Approved')
                return redirect(url_for("order_list",id=0))
            elif query_param=="Deny":
                order = Orders.query.get_or_404(id)
                order.status = "Denied"
                db.session.add(order)
                db.session.commit()
                flash('Order Denied')
                return redirect(url_for("order_list",id=0))
            else:
                flash("Something Went Wrong")
                return redirect(url_for("view_order",id=id))
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"SQLAlchemyError in register: {e}")
        flash('Error: Something Went Wrong', 'error')
    except Exception as e:
       logging.error(f"Error in expiry: {e}")
    return redirect(url_for("order_list",id=0))


@app.route("/logout",methods=["GET","POST"])
def logout():
    try:
        logout_user()
    except Exception as e:
       logging.error(f"Error in logout route: {e}")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run()
  

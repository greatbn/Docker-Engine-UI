from flask import Flask,render_template,session,request,flash,g,redirect,url_for
from flask.ext.bootstrap import Bootstrap
import sqlite3
import httplib, json,urllib
import os
app = Flask(__name__)
Bootstrap(app)

##Default parameters

alert = None
DATABASE = './hosts.db'
app.config.from_object(__name__)


### connect db

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

@app.before_request
def before_request():
	g.db  = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g,'db',None)
	if db is not None:
		db.close
## effect with restfull api
def get_api(path,method,host,port):
	g = httplib.HTTPConnection(host,port)
	headers = {"Content-type":"application/json"}
	g.request(method,path,"",headers)
	response = g.getresponse()
	
	return response

## index show total containers, images on host

@app.route("/", methods = ['GET','POST'])
def index():
	error = None

	all_info = []
	info = {} 
	info['count_run'] = None
	info['count_all_containers'] = None
	info['count_images'] = None
	info['status'] = None
	info['version'] = None
	info['OS'] = None
	info['Ram'] = None
	info['kernel'] = None
	info['cpu'] = None
	info['status'] = None
	try:
		conn_db = g.db.execute('select id,host,port from hosts order by id asc')
		list_host = conn_db.fetchall()
		
	except: 
		error = 'DATABASE Error'
		return render_template("index.html",all_info = all_info,error = error)
	
	for row in list_host:

		info['id'] = row[0]
		info['host'] = row[1]
		info['port'] = row[2]
		try:
			# get info docker
			info['count_run'] = len(json.loads(get_api(path = '/containers/json',method = 'GET',host=row[1],port=row[2]).read()))
			info['count_all_containers']  = len(json.loads(get_api(path = '/containers/json?all=1',method = 'GET',host=row[1],port=row[2]).read()))
			info['count_images'] = len(json.loads(get_api(path= '/images/json',method = 'GET',host=row[1],port=row[2]).read()))		

			#get info host
			more_info = json.loads(get_api(path='/info',method = 'GET',host=row[1],port=row[2]).read())

			info['version'] = more_info['ServerVersion']
			info['OS'] = more_info['OperatingSystem']
			info['Ram'] = more_info['MemTotal']
			info['kernel'] = more_info['KernelVersion']
			info['cpu'] = more_info['NCPU']
			info['status'] = 'OK'

			all_info.append(info.copy())
		except:

			info['status'] = 'Connection error'
			all_info.append(info.copy())
	if request.method=='POST':
		new_host = request.form['host']
		new_port = request.form['port']
		if new_host != '' and new_port != '':			
				if get_api(path='/info',method='GET',host= new_host,port = int(new_port)).status == 200:					
					try:
						conn = sqlite3.connect("./hosts.db")
						query = "insert into hosts(host,port) values('%s',%d)" %(new_host,int(new_port))
						
						conn.execute(query)
						
						conn.commit()
						conn.close()
						return redirect(url_for("index"))
					except:
						error = "DATABASE error"
						return render_template('index.html',all_info=all_info,error = error)					
				else:
					error = 'Host not available'
					return render_template('index.html',all_info = all_info,error = error)
		else:
			error  = 'Please type correct'
			return render_template("index.html",all_info = all_info,error = error)
					
	return render_template("index.html",all_info = all_info,error = error)

## list containers	
@app.route("/containers")
def containers():
	containers = []
	list_containers = {}
	list_containers['host'] = None
	list_containers['port'] = None
	list_containers['list_containers'] = []
	list_containers['node-name'] = None
	#id_host = request.args.get('id')
	try:
		query = "select id,host,port from hosts order by id asc"
		conn_db = g.db.execute(query)
		list_host = conn_db.fetchall()
	except: 
		error = 'DATABASE Error'
		return  render_template("containers.html",error = error,notify = request.args.get('stats'), alert = None)
	for row in list_host:
		list_containers['id'] = row[0]
		list_containers['host'] = row[1]
		list_containers['port'] = row[2]
		list_containers['node-name'] = json.loads(get_api(path='/info',method = 'GET',host=row[1],port=row[2]).read())['Name']
		if request.args.get('stats') == 'running':

			list_containers['list_containers'] = json.loads(get_api('/containers/json','GET',host = row[1],port= row[2]).read())
				#count = len(list_containers)
			containers.append(list_containers.copy())
		else:
			list_containers['list_containers'] = json.loads(get_api(path= '/containers/json?all=1',method = 'GET',host = row[1],port= row[2]).read())
			containers.append(list_containers.copy())
	return render_template("containers.html",containers = containers,notify = request.args.get('stats'), alert = None)


@app.route("/containers/<host_id>")
def containers_in_hosts(host_id):
	containers = []
	list_containers = {}
	list_containers['host'] = None
	list_containers['port'] = None
	list_containers['list_containers'] = []
	list_containers['node-name'] = None
	#id_host = request.args.get('id')
	try:
		query = "select id,host,port from hosts where id = "+ host_id
		conn_db = g.db.execute(query)
		host = conn_db.fetchall()
		
	except: 
		error = 'DATABASE Error'
		return  render_template("containers.html",error = error,notify = request.args.get('stats'), alert = None)
	list_containers['id'] = host[0][0]
	list_containers['host'] = host[0][1]
	list_containers['port'] = host[0][2]
	list_containers['node-name'] = json.loads(get_api(path='/info',method = 'GET',host=host[0][1],port=host[0][2]).read())['Name']
	if request.args.get('stats') == 'running':

		list_containers['list_containers'] = json.loads(get_api('/containers/json','GET',host = host[0][1],port= host[0][2]).read())
				#count = len(list_containers)
		containers.append(list_containers.copy())
	else:
		list_containers['list_containers'] = json.loads(get_api(path= '/containers/json?all=1',method = 'GET',host = host[0][1],port= host[0][2]).read())
		containers.append(list_containers.copy())
	return render_template("containers.html",containers = containers,notify = request.args.get('stats'), alert = None)



##define action in containers and images	
@app.route("/action")
def action():
	host_id = request.args.get('host_id')
	id_con = request.args.get('id')
	action =  request.args.get('action')
	object_effect = request.args.get('object')
	try:
		query = 'select id,host,port from hosts where id = '+host_id
		conn_db = g.db.execute(query)
		host = conn_db.fetchall()
		
	except: 
		error = 'DATABASE Error'
		return render_template(object_effect+".html",error = error)

	if object_effect=='images' and action == 'pull':
		alert = get_api(path='/images/create?fromImage='+id_con,method='POST',host = host[0][1],port = host[0][2]).status
	elif action == 'remove':
		alert = get_api(path='/'+object_effect+'/'+id_con,method='DELETE',host = host[0][1],port = host[0][2]).status
	else:
		alert = get_api(path= '/'+object_effect+'/'+id_con+'/'+action,method = 'POST',host = host[0][1],port = host[0][2]).status
	payload = json.loads(get_api('/'+object_effect+'/json','GET',host = host[0][1],port = host[0][2]).read())
	count = len(payload)
	if object_effect =='images':
		return redirect(url_for('images',host_id = host_id))
	elif object_effect == 'containers':
		return redirect(url_for('containers_in_hosts',host_id = host_id))


#remove host
@app.route('/remove')
def remove():
	id = int(request.args.get('id'))

	try:
		query = "delete from hosts where id=%d" %id			
		g.db.execute(query)		
		g.db.commit()
		#conn.close()
		return redirect(url_for('index'))
	except:
		error = 'DATABASE Error'
		return render_template('index.html',error = error)



##  list images from host

@app.route("/images/<host_id>",methods = ['GET','POST'])
def images(host_id):
	error = None
	try:
		query = 'select id,host,port from hosts where id = '+host_id
		conn_db = g.db.execute(query)
		host = conn_db.fetchall()
	except: 
		error = 'DATABASE Error'
		return render_template("images.html",error = error)
	try:	
		payload_image = json.loads(get_api(path='/images/json',method='GET',host = host[0][1],port = host[0][2]).read())
		count = len(payload_image)
	except:
		error = "Docker Host error"
		return render_template("images.html",error = error)
	if request.method =='POST':	
		return redirect(url_for('search',host_id = host_id ,image_name_search = request.form['image_name']))
	return render_template("images.html",payload = payload_image,error= error,host_id = host_id)

## search image
@app.route("/search/<host_id>/<image_name_search>")
def search(host_id,image_name_search):
	error = None
	try:
		query = 'select id,host,port from hosts where id = '+host_id
		conn_db = g.db.execute(query)
		host = conn_db.fetchall()
	except: 
		error = 'DATABASE Error'
		return render_template("images.html",error = error)
	payload_image_search = json.loads(get_api(path='/images/search?term='+image_name_search,method = 'GET',host= host[0][1],port = host[0][2]).read())
	
	return render_template("image_search.html",payload = payload_image_search , image_name = image_name_search,host_id = host_id)

#info host

@app.route("/info/<host_id>")
def info(host_id):
	error = None
	try:
		query = 'select id,host,port from hosts where id = '+host_id
		conn_db = g.db.execute(query)
		host = conn_db.fetchall()
	except: 
		error = 'DATABASE Error'
		return render_template("index.html",error = error)
	payload_info = json.loads(get_api(path='/info',method = 'GET',host=host[0][1],port = host[0][2]).read())
	return render_template("info.html",payload = payload_info)

if __name__ == '__main__':
	port = int(os.environ.get("PORT", 5000))
	app.run(host ='0.0.0.0',port=port,debug = True)

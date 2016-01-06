from flask import Flask,render_template,session,request,flash,g,redirect,url_for
from flask.ext.bootstrap import Bootstrap
import sqlite3
import httplib, json,urllib
app = Flask(__name__)
Bootstrap(app)

##Default parameters

alert = None
DATABASE = './hosts.db'
app.config.from_object(__name__)


## effect with restfull api
def connect_db():
	return sqlite3.connect(app.config['DATABASE'])
def get_db():
	if not hasattr(g,'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db

def get_api(path,method,host,port):
	g = httplib.HTTPConnection(host,port)
	headers = {"Content-type":"application/json"}
	g.request(method,path,"",headers)
	response = g.getresponse()
	
	return response
@app.route("/settings",methods = ['GET','POST'])
def settings():
	if request.method =='POST':
		host = request.form['host']
		port = request.port['port']
		return redirect(url_for("index"))
	return render_template("settings.html")

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
		db = get_db()
		conn_db = db.execute('select id,host,port from hosts order by id asc')
		list_host = conn_db.fetchall()
		db.close()
		#print list_host
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
		print new_host
		print new_port
		if new_host != '' and new_port != '':			
				if get_api(path='/info',method='GET',host= new_host,port = int(new_port)).status == 200:					
					try:
						conn = sqlite3.connect("./hosts.db")
						query = "insert into hosts(host,port) values('%s',%d)" %(new_host,int(new_port))
						print query
						conn.execute(query)
						print 'ok'
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
					
	#return all_info[0]		
	return render_template("index.html",all_info = all_info,error = error)

## list containers	
@app.route("/containers")
def containers():
	try:
		db = get_db()
		conn_db = db.execute('select id,host,port from hosts order by id asc')
		list_host = conn_db.fetchall()
		db.close()
		#print list_host
	except: 
		error = 'DATABASE Error'
		return  render_template("containers.html",payload = payload,count = count,notify = request.args.get('stats'), alert = None)
	for row in list_host:
		if request.args.get('stats') == 'running':
			payload = json.loads(get_api('/containers/json','GET').read(),host = row[1],port= row[2])
			count = len(payload)
		else:
			payload = json.loads(get_api(path= '/containers/json?all=1',method = 'GET',host = row[1],port= row[2]).read())
			count = len(payload)
	return render_template("containers.html",payload = payload,count = count,notify = request.args.get('stats'), alert = None)


##define action in containers and images	
@app.route("/action")
def action():
	id_con = request.args.get('id')
	action =  request.args.get('action')
	object_effect = request.args.get('object')
	if object_effect=='images' and action == 'pull':
		alert = get_api(path='/images/create?fromImage='+id_con,method='POST').status
	elif action == 'remove':
		alert = get_api(path='/'+object_effect+'/'+id_con,method='DELETE').status
	else:
		alert = get_api(path= '/'+object_effect+'/'+id_con+'/'+action,method = 'POST').status
	payload = json.loads(get_api('/'+object_effect+'/json','GET').read())
	count = len(payload)
	return render_template(object_effect+".html",payload = payload,count = count,notify = request.args.get('stats'), alert = alert )

#remove host
@app.route('/remove')
def remove():
	id = int(request.args.get('id'))

	try:
		query = "delete from hosts where id=%d" %id
		conn = get_db()				
		conn.execute(query)		
		conn.commit()
		#conn.close()
		return redirect(url_for('index'))
	except:
		error = 'DATABASE Error'
		return render_template('index.html',error = error)


##  list images

@app.route("/images",methods = ['GET','POST'])
def images():
	try:
		db = get_db()
		conn_db = db.execute('select id,host,port from hosts order by id asc')
		list_host = conn_db.fetchall()
		db.close()
		#print list_host
	except: 
		error = 'DATABASE Error'
		return  render_template("containers.html",payload = payload,count = count,notify = request.args.get('stats'), alert = None)
	for row in list_host:
		payload_image = json.loads(get_api(path='/images/json',method='GET').read())
		count = len(payload_image)
		if request.method =='POST':		
			return redirect(url_for('search',image_name_search = request.form['image_name']))
	return render_template("images.html",payload = payload_image,count = count)

## search image
@app.route("/search/<image_name_search>")
def search(image_name_search):
	payload_image_search = json.loads(get_api(path='/images/search?term='+image_name_search,method = 'GET').read())
	count = len(payload_image_search)
	return render_template("image_search.html",payload = payload_image_search , count = count,image_name = image_name_search)
if __name__ == '__main__':
	app.run(host ='0.0.0.0',debug = True)
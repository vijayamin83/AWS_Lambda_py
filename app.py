from flask import Flask, render_template, url_for, request
import boto3, zipfile, os, json, sqlite3 

iam_client = boto3.client('iam')
lambda_client = boto3.client('lambda')
app = Flask(__name__)

# class for error handaling
class ResourceConflictException(Exception): pass

# create database;
conn = sqlite3.connect('templates/awslambda.db')
c = conn.cursor()

def create_table():
	c.execute('CREATE TABLE IF NOT EXISTS lambda_function( id integer PRIMARY KEY AUTOINCREMENT, fun_name text not null, action text NOT NULL, res_lambda text default null, res_invoke text default null);')

create_table()

# def data_entry():
# 	c.execute('INTER INTO lambda_function VALUES(1,"fun_name","action","res_lambda","res_invoke")');
# 	conn.commit()
# 	c.close()
# 	conn.close()
#data_entry()

# set route "/"
@app.route('/')
def index():
   return render_template('index.html')

# role = iam_client.get_role(RoleName='FullAccess-Lambda-DynamoDB')
# print(role)
@app.route('/', methods=['POST'])

def getvalue():
	# get zip file request
	fileUpload=request.files['photo']
	#print (fileUpload)

	# get the all require variables    
	funName=request.form['funName']
	funName=funName.replace(" ", "-")
	runTime=request.form['runTime'] #"nodejs10.x"
	role=request.form['role'] #"arn:aws:iam::112911278656:role/proximity-serverless-dev-us-east-1-lambdaRole"
	handler=request.form['handler'] # index.handler
	ltype=request.form['ltype'] #"Hello test file write"
	event=request.form['event'] # event file in json format
	env_=request.form['env_']	# environment var. in json format
	ext=request.form['ext']	# get extention
	code=request.form['code']	# get extention
	upload_opt=request.form['upload_opt']	# upload option (zip or textarea)
	Timeout=300

	# set event and env_ variable defautl if are balnk
	if event == "":
		event = "{}"
	if env_ == "":
		env_ = "{}"
	
	# create folder, file and write code into folder
	# strnew=handler.split(".",2)
	# filename=strnew[0] + ".js"
	# zipFileName=funName + ".zip"

	if(upload_opt == 'zip'):

		# save file to folder
		fileUpload.save(os.path.join('files/', fileUpload.filename))

		# set file name
		zipFileName=fileUpload.filename
		# set file location
		fileCode='files/' + fileUpload.filename
	elif(upload_opt == 'textarea'):
		# create folder, file and write code into folder
		strnew=handler.split(".",2)
		filename=strnew[0] + "."+ext
		zipFileName=funName + ".zip"

		# write code into file
		f = open(filename, "w")
		f.write(code)
		f.close()

		# create zip file
		zipObj = zipfile.ZipFile(zipFileName, 'w')
		zipObj.write(filename)
		zipObj.close()

		fileCode = zipFileName


	#print (fileUpload)


	# file process
	zipped_code = fileProcess(fileCode)
	# remove zip file
	os.remove(fileCode);	
	
	# create object
	botoObj = {
	  "FunctionName":funName,
	  "Runtime":runTime,
	  "Role":role,
	  "Handler":handler,
	  "ZipFile":zipped_code,
	  "Environment":{
        "Variables": json.loads(env_)
      },
	  "Timeout":300
	  }

	print (botoObj)
	# call to createLamdaFunction method
	resLambda = createLamdaFunction(botoObj)

	print(resLambda)

	#insQue = "INSERT INTO lambda_function VALUES('"+funName+"',"

	#,"##lambda##","'+resLambda+'"'


	if ltype == 'lambda_invoke':
		resInvoke = lambdaInvoke(funName,event)
		
		pay_ = resInvoke['Payload']
		pay_res = pay_.read().decode("utf-8")
		print ("PAYLOAD RESPONSE")
		print (pay_res)
		
		#insQue = insQue + "'lambda_invoke', '"+json.dumps(resLambda)+"','"+ bytes(json.dumps(resInvoke)).escape()+"')"
	else:
		resInvoke = ""
		#insQue = insQue + "'lambda', '"+json.dumps(resLambda)+"',null)"

	print ("########## sqlite query \n\n")
	#print (insQue)	

	# c.execute(insQue)
	# c.close()
	# conn.close()

	
		
	resLambda["success"] = 	"LAMBDA CREATED SUCCESSFULLY!!"

	return render_template('index.html',res_lambda=resLambda, res_invoke=resInvoke)

def createLamdaFunction(botoObj):
	#print(botoObj)
	try:
		response = lambda_client.create_function(
		  FunctionName=botoObj['FunctionName'],
		  Runtime=botoObj['Runtime'],
		  Role=botoObj['Role'],
		  Handler=botoObj['Handler'],
		  Code=dict(ZipFile=botoObj['ZipFile']),
		  Timeout=botoObj['Timeout'],
		  Environment=botoObj['Environment']
		)
		#response  = 19 - 9
		print(response)
		# lambda_client.
		#print(response)
	except:
  		print ("lamdbaError==")
  		raise ResourceConflictException('An error occurred (ResourceConflictException) when calling the CreateFunction operation: Function already exist' + botoObj['FunctionName'])
	else:
		print ("LAMBDA CREATED SUCCESSFULLY!!")
		return response

def lambdaInvoke(funName,event):
	res=lambda_client.invoke(
	    FunctionName=funName,
	    InvocationType='Event',
	    LogType='Tail',
	    Payload=event
	)
	print ("LAMBDA INVOKE RESPONSE..")
	print (res)
	return res


def fileProcess(fileCode):
	
	# # make zip file of the folder
	# # os.makedirs(os.path.dirname(filename), exist_ok=True)	
	# with open(filename, "w") as f: f.write(fileCode)

	# zf = zipfile.ZipFile(zipFileName, mode='w')
	# try:
	#     #print ('adding README.txt')
	#     zf.write(filename)
	# finally:
	#     #print ('closing')
	#     zf.close()

	# map with boto3 object to create lambda function

	iam_client = boto3.client('iam')
	lambda_client = boto3.client('lambda')
	env_variables = dict() # Environment Variables
	with open(fileCode, 'rb') as f:
	  zipped_code = f.read()
	#print(zipped_code)

	return zipped_code




if __name__ == '__main__':
   app.run(debug = True)
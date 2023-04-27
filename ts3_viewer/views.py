from django.shortcuts import render
from django.template import loader
from django.core.files.storage import FileSystemStorage
import os
import re

data=None

# Create your views here.
def index(request):
    dir = 'ts3_viewer/static/media'
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))
    template=loader.get_template('ts3_viewer/index.html')
    global data 
    data= None
    return render(request,'ts3_viewer/index.html')




"""
This function returns the data that  will be shown at the result's page

Args:
file_url(str)
language(str)

Returns:
dictionary with the list of registers, list of dates, the hours and minutes 
"""
def dataCollector(file_url,language):
    lines_cleaned=[]
    daySeparator=''
    #registers and dates are supposed to be parallel lists
    registers=[]
    dates=[]
    day_registers=[]
    if language =='spanish':
        daySeparator='*** El registro comienza'
    elif language =='english':
        daySeparator='*** Log begins'
    

    arch=open(os.getcwd()+file_url, "r", encoding="utf-8")
    lines=arch.readlines()
    pattern = re.compile('<.*?>')
    
    for i in lines:
        l=re.sub(pattern, '', i)
        l=l.replace('\n','')
        l=l.replace('&lt;','')
        l=l.replace('\"','\'')
        l=l.replace('&quot;','\'')
        l=l.replace('&gt;','')
        l=l.replace('&nbsp;','')
        
        if "movió" in l:
            #i added this because there's a error when i remove characters in spanish logs
            l=l.replace("movió"," movió")
        lines_cleaned.append(l)

    

    for j in lines_cleaned:

        if (daySeparator in j):
            d=j.split()[-2]
            if d not in dates: 
                
                registers.append(day_registers)
                day_registers=[]
                dates.append(d)
        else:
            day_registers.append(j)
    registers.append(day_registers)   

    arch.close()
    hours=[]
    minutes=[]

    for i in range(24):
        if i<10:
            hours.append('0'+str(i))
        else:
            hours.append(str(i))

    for i in range(60):
        if i<10:
            minutes.append('0'+str(i))
        else:
            minutes.append(str(i))

    return {'language':language,'sep_registers':registers,'dates_list':dates,'hstart':hours,'hend':hours,'mstart':minutes,'mend':minutes}




    

def results(request):
    global data
    if request.method=='POST' and 'uploadedfile' in request.FILES:
        upload = request.FILES['uploadedfile']
        fss = FileSystemStorage()
        file = fss.save(upload.name, upload)
        file_url = fss.url(file)
        if 'spanish' in request.POST['optionsRadios']:
            
            data=dataCollector(file_url,'spanish')
            context={'dates_list':data['dates_list'],'hstart':data['hstart'],'hend':data['hend'],'mstart':data['mstart'],'mend':data['mend'],'consulting':0}
            return render(request,'ts3_viewer/results.html',context)
        elif 'english' in request.POST['optionsRadios']:
            data=dataCollector(file_url,'english')
            context={'dates_list':data['dates_list'],'hstart':data['hstart'],'hend':data['hend'],'mstart':data['mstart'],'mend':data['mend'],'consulting':0}
            return render(request,'ts3_viewer/results.html',context)
        
    elif request.method == 'GET':
        room_name=request.GET['cname']
        room_name_clean=room_name.replace(' ','')
        date_pointer=data['dates_list'].index(request.GET['date_selected'])+1
        info_to_show=[]

        reg_of_selected_date=data['sep_registers'][date_pointer]
        reg_of_selected_time=[]
        

       
        DISCONNECTED=''
        SWITCHED=''
        MOVED=''
        if data['language'] == 'spanish':
            DISCONNECTED='desconectó'
            SWITCHED='cambió'
            MOVED='movió'
        elif data['language'] == 'english':
            DISCONNECTED='disconnected'
            SWITCHED='switched'
            MOVED='moved'
        
        
        movements={}
        users={}

        tstart=int(request.GET['hs'])*60+int(request.GET['ms'])
        tend=int(request.GET['he'])*60+int(request.GET['me'])

        for k in reg_of_selected_date:
            sep=k.split()
            actualtime=int(sep[0].split(":")[0])*60+int(sep[0].split(":")[1])
            if (actualtime>=tstart) and (actualtime<=tend):
                reg_of_selected_time.append(k)

        reg_of_day_clean=[]
        #Here i remove the spaces found in the nicknames and the room names, those room names are inside quotes ''
        #For example i have this 'this is a user', 'this is a room', and i receive 'thisisauser', 'thisisaroom'
        for i in reg_of_selected_time:
            s=''
            b=False
            for j in i:
                if (j == "'") and (b==False):
                    b=True
                elif (j == "'") and (b==True):
                    b=False
                if b:
                    if (j != " "):
                        s+=j
                else:
                    s+=j
            reg_of_day_clean.append(s)

        for j in reg_of_day_clean:
            sep=j.split()
            if  (SWITCHED in j) and (room_name_clean in sep[-1]):
                movements[j]=1
                users[sep[1]]=1
            elif (SWITCHED in j) and (room_name_clean in sep[-3]):
                movements[j]=0
                users[sep[1]]=0
            if data['language'] == 'english':
                if (MOVED in j) and (room_name_clean in sep[-3]):
                    movements[j]=1
                    users[sep[1]]=1
                elif (MOVED in j) and (room_name_clean in sep[-5]):
                    movements[j]=0
                    users[sep[1]]=0
            elif data['language'] == 'spanish':
                if (MOVED in j) and (room_name_clean in sep[-1]):
                    movements[j]=1
                    users[sep[3]]=1
                elif (MOVED in j) and (room_name_clean in sep[-3]):
                    movements[j]=0
                    users[sep[3]]=0

            if (DISCONNECTED in j):
                
                if(sep[1] in users):
                    movements[j]=0
                    users[sep[1]]=0
            
                




        
        


        context={'movements':movements,'users':users,'dates_list':data['dates_list'],'hstart':data['hstart'],'hend':data['hend'],'mstart':data['mstart'],'mend':data['mend'],
                 'consulting':1,'room':request.GET['cname'],'sel_date':request.GET['date_selected'],'hssel':request.GET['hs'],'mssel':request.GET['ms'],
                 'hesel':request.GET['he'],'mesel':request.GET['me']}
        return render(request,'ts3_viewer/results.html',context)
        
    return render(request,'ts3_viewer/index.html')








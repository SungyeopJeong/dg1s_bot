# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template
import datetime
from pytz import timezone, utc
import openpyxl
import requests
from bs4 import BeautifulSoup
from pytz import timezone, utc

application=Flask(__name__)

Days=["일요일","월요일","화요일","수요일","목요일","금요일","토요일"] # 요일 이름
mday=[31,28,31,30,31,30,31,31,30,31,30,31] # 매월 일 수
Msg=[["[오늘 아침]","[오늘 점심]","[오늘 저녁]"],["[내일 아침]","[내일 점심]","[내일 저녁]"]] # 급식 title
Menu = [["","",""],["","",""]] # 오늘, 내일 급식
classn=["11","12","13","14","21","22","23","24","31","32","33","34"] # 반 이름
classN=[20,20,20,21,20,19,19,19,14,13,10,11] # 반 학생 수
Timetable=[[[["1반","생명B(1,2반)","수학A","물리B","물리B","수학B","봉사","자율","1반"],
             ["1반","음악","음악","영어A(1,2반)","국어B","화학B","화학B","동아리","1반"],
             ["1반","수학B","수학A","방학식","방학","방학","방학","방학","방학"],
             ["방학","방학","방학","방학","방학","방학","방학","방학","방학"],
             ["방학","방학","방학","방학","방학","방학","방학","방학","방학"]],
            [["2반","진로","국어B","화학B","화학B","영어A(1,2반)","봉사","자율","2반"],
             ["2반","생명B(1,2반)","생명A","수학A","수학B","지학A","지학A","동아리","2반"],
             ["2반","영어A(1,2반)","화학A","방학식","방학","방학","방학","방학","방학"],
             ["방학","방학","방학","방학","방학","방학","방학","방학","방학"],
             ["방학","방학","방학","방학","방학","방학","방학","방학","방학"]],
            [["3반","음악","음악","수학B","영어A(3,4반)","국어B","봉사","자율","3반"],
             ["3반","물리B","물리B","생명B(3,4반)","화학A","지학B","지학B","동아리","3반"],
             ["3반","체육(3반)","생명B(3,4반)","방학식","방학","방학","방학","방학","방학"],
             ["방학","방학","방학","방학","방학","방학","방학","방학","방학"],
             ["방학","방학","방학","방학","방학","방학","방학","방학","방학"]],
            [["4반","국어B","지학A","지학A","수학A","체육(4반)","봉사","자율","4반"],
             ["4반","영어A(3,4반)","수학A","수학B","진로","음악","음악","동아리","4반"],
             ["4반","수학A","수학B","방학식","방학","방학","방학","방학","방학"],
             ["방학","방학","방학","방학","방학","방학","방학","방학","방학"],
             ["방학","방학","방학","방학","방학","방학","방학","방학","방학"]]],
           [[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]]],
           [[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]]]]
#변동사항

KST=timezone('Asia/Seoul')
now=datetime.datetime.utcnow()
date=int(utc.localize(now).astimezone(KST).strftime("%d"))-1
month=int(utc.localize(now).astimezone(KST).strftime("%m"))
year=int(utc.localize(now).astimezone(KST).strftime("%Y"))

def prin(datas,classN):
    
    KST=timezone('Asia/Seoul') #현재 시간
    now=datetime.datetime.utcnow()
    day=int(utc.localize(now).astimezone(KST).strftime("%w"))
    answer=""
    subName=datas[0]; subType=datas[1]; #datas: 0=name, 1=type, 2=zoomid, 3=zoompwd, 4=hangoutid, 5=class, 6=teacher
    if subType=="daymeeting":
        answer+=Days[day]+" ["+subName
        if classN==0 : answer+=" 조례]\n"
        elif classN==8 : answer+=" 종례]\n"
        answer+="https://zoom.us/j/"+datas[2]+"?pwd="+datas[3];
    elif subType=="club":
        answer+=Days[day]+" "+str(classN)+"교시 지금은 동아리 시간입니다."
    else :
        answer+=Days[day]+" "+str(classN)+"교시 : ["+subName+"]\n"
        if subType=="none":
            answer+="(해당 클래스룸이 개설되지 않았습니다.)"
        else :
            if subType=="zoom":
                answer+="줌 : https://zoom.us/j/"+datas[2]+"?pwd="+datas[3]+"\n"
            elif subType=="hangout":
                answer+="행아웃 : https://meet.google.com/lookup/"+datas[4]+"\n"
            answer+="클래스룸 : https://classroom.google.com/u/0/c/"+datas[5]
    return answer

@application.route('/link', methods=['POST'])
def response_link(): # 온라인 클래스 링크 대답 함수
    
    KST=timezone('Asia/Seoul') #현재 시간
    now=datetime.datetime.utcnow()
    day=int(utc.localize(now).astimezone(KST).strftime("%w"))
    hour=int(utc.localize(now).astimezone(KST).strftime("%H"))
    minutes=int(utc.localize(now).astimezone(KST).strftime("%M"))
    classN=0
    if (hour == 8 and minutes < 23): classN=0 # 8:20~8:40
    elif ((hour == 8 and minutes >= 23) or (hour == 9 and minutes < 20)): classN=1 # 8:40~9:30
    elif ((hour == 9 and minutes >= 20) or (hour == 10 and minutes < 20)): classN=2 # 9:40~10:30
    elif ((hour == 10 and minutes >= 20) or (hour == 11 and minutes < 20)): classN=3 # 10:40~11:30
    elif ((hour == 11 and minutes >= 20) or (hour == 12 and minutes < 20)): classN=4 # 11:40~12:30
    elif (hour == 13): classN=5 # 13:20~14:10
    elif (hour == 14): classN=6 # 14:20~15:10
    elif (hour == 15): classN=7 # 15:20~16:10
    elif (hour == 16 and minutes <= 20): classN=8 # 16:10~16:20
    else : classN=9 # 수업 없음
        
    req=request.get_json() # 파라미터 값 불러오기
    userid=req["userRequest"]["user"]["properties"]["plusfriendUserKey"]
    stid="none"
    
    fr=open("/home/ubuntu/dg1s_bot/user data.txt","r") # 학번 불러오기
    lines=fr.readlines()
    fr.close()
    fw=open("/home/ubuntu/dg1s_bot/user data.txt","w")
    for line in lines:
        datas=line.split(" ")
        dusid=datas[0]; dstid=datas[1];
        if dusid==userid: stid=dstid
        fw.write(line)
    fw.close()
    if stid=="none":
        res={
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "basicCard": {
                            "title": "[학번 등록]",
                            "description": "학번이 등록되어 있지 않습니다.\n아래 버튼을 눌러 학번을 등록해주세요",
                            "buttons": [ { "action": "message", "label": "학번 등록", "messageText": "학번 등록" } ]
                        }
                    }
                ]
            }
        }
    else :
        if day==6 or day==0 or classN==9: answer="진행 중인 수업이 없습니다."
        else :
            grade=int(stid[0]); classn=int(stid[1])
            subjectName=Timetable[grade-1][classn-1][day-1][classN]
            fr=open("/home/ubuntu/dg1s_bot/subject data.txt","r") # 과목 정보 불러오기
            lines=fr.readlines()
            fr.close()
            fw=open("/home/ubuntu/dg1s_bot/subject data.txt","w")
            for line in lines:
                datas=line.split(" ")
                dname=datas[0]; dtype=datas[1]; dzoomid=datas[2];
                dzoompwd=datas[3]; dhangoutid=datas[4]; dclass=datas[5];
                if dname==subjectName: answer=prin(datas,classN)
                fw.write(line)
            fw.close()
        res={
            "version": "2.0",
            "template": {
                "outputs": [ { "simpleText": { "text": answer } } ]
            }
        }
    return jsonify(res)

@application.route('/seat', methods=['POST'])
def input_seat(): # 좌석 입력 함수
    
    now=datetime.datetime.utcnow() # Meal 계산
    Day=int(utc.localize(now).astimezone(KST).strftime("%w"))
    hour=int(utc.localize(now).astimezone(KST).strftime("%H"))
    minu=int(utc.localize(now).astimezone(KST).strftime("%M"))
    if (hour==6 and minu>=50) or (hour>=7 and hour<12) or (hour==12 and minu<10): Meal="아침"
    elif (hour==12 and minu>=10) or (hour>=13 and hour<18) or (hour==18 and minu<10): Meal="점심"
    else:
        Meal="저녁"
        if (hour==6 and minu<50) or hour<=5 : Day=(Day+6)%7
        
    req=request.get_json() # 파라미터 값 불러오기
    userid=req["userRequest"]["user"]["properties"]["plusfriendUserKey"]
    day=req["action"]["detailParams"]["sys_date"]["value"]
    meal=req["action"]["detailParams"]["seat_menu"]["value"]
    seat=int(req["action"]["detailParams"]["table_seat"]["value"])
    p1=req["action"]["detailParams"]["student_id"]["value"]
    p2=req["action"]["detailParams"]["student_id1"]["value"]
    stid="none"; invt=False; cday=0; ciday=0
    
    if day!="7": # 유효한 날짜값인지 계산
        if day.split('"')[3]=="dateTag" : invt=True
        else :
            iyear=int(day.split('"')[3][:4])
            imonth=int(day.split('"')[3][5:7])
            idate=int(day.split('"')[3][8:])
            cday=(year-1)*365+(year-1)//4-(year-1)//100+(year-1)//400;
            ciday=(iyear-1)*365+(iyear-1)//4-(iyear-1)//100+(iyear-1)//400;
            if (year%4==0 and year%100!=0) or year%400==0: cday+=1
            if (iyear%4==0 and iyear%100!=0) or iyear%400==0: ciday+=1
            for i in range(0,month-1): cday+=mday[i]
            for i in range(0,imonth-1): ciday+=mday[i]
            cday+=date+1; ciday+=idate
            if (hour==6 and minu<50) or hour<=5 : cday-=1
            if cday-ciday>=0 and cday-ciday<=(Day+6)%7 : invt=False
            else : invt=True
            day=ciday%7
    if meal!="none" and cday==ciday: 
        if Meal=="아침" and meal!="아침": invt=True
        elif Meal=="점심" and meal=="저녁": invt=True
            
    if invt==True: #유효하지 않은 날짜값
        res={
            "version": "2.0",
            "template": { "outputs": [ { "simpleText": { "text": "유효하지 않은 날짜/시간 값입니다." } } ] }
        }
    else :
        fr=open("/home/ubuntu/dg1s_bot/user data.txt","r") # userdata 저장 및 변경
        lines=fr.readlines()
        fr.close()
        fw=open("/home/ubuntu/dg1s_bot/user data.txt","w")
        for line in lines:
            datas=line.split(" ")
            dusid=datas[0]; dstid=datas[1]; dday=datas[2]; dmeal=datas[3]
            dseat=int(datas[4]); dp1=datas[5]; dp2=datas[6].rstrip()
            if dusid==userid:
                stid=dstid
                if dday!="7" and day=="7": day=int(dday)
                if dday=="7" and day=="7": day=Day
                if dmeal!="none" and meal=="none": meal=dmeal
                if dmeal=="none" and meal=="none": meal=Meal
                seat=dseat if seat==0 else seat
                if p1=="none" and p2=="none":
                    p1=dp1; p2=dp2
                elif p1!="none" and p2=="none":
                    if dp1=="none" and dp2=="none": p1=p1; p2=dp2
                    elif dp1!="none" and dp2=="none": p2=p1; p1=dp1
                    elif dp1!="none" and dp2!="none": p2=p1; p1=dp2
            else : fw.write(line)
        if day=="7": day=Day
        if meal=="none": meal=Meal
        if p2==stid or p2==p1: p2="none"
        if p1==stid: p1="none"
        fw.write(userid+" "+stid+" "+str(day)+" "+meal+" "+str(seat)+" "+p1+" "+p2+"\n")
        fw.close()
        
        if stid=="none": # 등록 안된 user
            res={
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "basicCard": {
                                "title": "[학번 등록]",
                                "description": "학번이 등록되어 있지 않습니다.\n아래 버튼을 눌러 학번을 등록해주세요",
                                "buttons": [ { "action": "message", "label": "학번 등록", "messageText": "학번 등록" } ]
                            }
                        }
                    ]
                }
            }
        else:
            stids=stid # 저장 확인
            if p1!="none" and p1!=stid: stids+=", "+p1 
            if p2!="none" and p2!=stid and p2!=p1: stids+=", "+p2
            res={
                    "version": "2.0",
                    "template": {
                        "outputs": [
                            {
                                "carousel": {
                                    "type": "basicCard",
                                    "items": [
                                        {
                                            "title": "[저장 확인]",
                                            "description": "학번    "+stids+"\n날짜    "+Days[day]+"\n식사    "+meal+"\n좌석    "+str(seat),
                                            "buttons": [
                                                { "action": "message", "label": "확인", "messageText": "확인했습니다." },
                                                { "action": "message", "label": "초기화", "messageText": "초기화" }
                                            ]
                                        },
                                        { 
                                            "thumbnail":{
                                                "imageUrl": "http://k.kakaocdn.net/dn/m2tci/btqOvcSDnnh/STY3XTAYC37ce8RYvulrX0/img_l.jpg", "fixedRatio": "true"
                                            } 
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }  
    return jsonify(res)

@application.route('/stid', methods=['POST'])
def input_stid(): # 학번 입력 함수
        
    req=request.get_json() # 파라미터 값 불러오기
    userid=req["userRequest"]["user"]["properties"]["plusfriendUserKey"]
    stid=req["action"]["detailParams"]["student_id"]["value"]
    
    fr=open("/home/ubuntu/dg1s_bot/user data.txt","r") # userdata 저장 및 변경
    lines=fr.readlines()
    fr.close()
    fw=open("/home/ubuntu/dg1s_bot/user data.txt","w")
    for line in lines:
        datas=line.split(" ")
        dusid=datas[0]; dstid=datas[1];
        if dusid==userid:
            fw.write(userid+" "+stid+" 7 none 0 none none\n")
        else : fw.write(line)
    fw.close()
    res={
        "version": "2.0",
        "template": { "outputs": [ { "simpleText": { "text": "학번이 "+stid+"(으)로 등록되었습니다." } } ] }
    }
    return jsonify(res)

@application.route('/save', methods=['POST'])
def final_save(): # 최종 저장 함수
    
    now=datetime.datetime.utcnow() # Meal 계산
    Day=int(utc.localize(now).astimezone(KST).strftime("%w"))
    hour=int(utc.localize(now).astimezone(KST).strftime("%H"))
    minu=int(utc.localize(now).astimezone(KST).strftime("%M"))
    if (hour==6 and minu>=50) or (hour>=7 and hour<12) or (hour==12 and minu<10): Meal="아침"
    elif (hour==12 and minu>=10) or (hour>=13 and hour<18) or (hour==18 and minu<10): Meal="점심"
    else:
        Meal="저녁"
        if (hour==6 and minu<50) or hour<=5 : Day=(Day+6)%7
    
    req=request.get_json() # 파라미터 값 불러오기
    userid=req["userRequest"]["user"]["properties"]["plusfriendUserKey"]
    
    fr=open("/home/ubuntu/dg1s_bot/user data.txt","r") # 좌석 저장 후 초기화
    lines=fr.readlines()
    fr.close()
    rw=open("/home/ubuntu/dg1s_bot/user data.txt","w")
    fw=open("/home/ubuntu/dg1s_bot/final save.txt","a")
    for line in lines:
        datas=line.split(" ")
        dusid=datas[0]; dstid=datas[1]; dday=int(datas[2]); dmeal=datas[3]
        dseat=int(datas[4]); dp1=datas[5]; dp2=datas[6].rstrip()
        if dmeal=="아침": dmeal="0"
        elif dmeal=="점심": dmeal="1"
        elif dmeal=="저녁": dmeal="2"
        if dusid==userid:
            fw.write(dstid+" "+str(dday)+" "+dmeal+" "+str(dseat)+" -\n")
            if dp1!="none": fw.write(dp1+" "+str(dday)+" "+dmeal+" "+str(dseat)+" *\n")
            if dp2!="none": fw.write(dp2+" "+str(dday)+" "+dmeal+" "+str(dseat)+" *\n")
            rw.write(userid+" "+dstid+" 7 none 0 none none\n")
        else : rw.write(line) 
    rw.close()
    fw.close()
    
    res={
        "version": "2.0",
        "template": { "outputs": [ { "simpleText": { "text": "저장되었습니다." } } ] }
    }
    return jsonify(res)

@application.route('/reset', methods=['POST'])
def reset(): # 초기화
    
    now=datetime.datetime.utcnow() # Meal 계산
    Day=int(utc.localize(now).astimezone(KST).strftime("%w"))
    hour=int(utc.localize(now).astimezone(KST).strftime("%H"))
    minu=int(utc.localize(now).astimezone(KST).strftime("%M"))
    if (hour==6 and minu>=50) or (hour>=7 and hour<12) or (hour==12 and minu<10): Meal="아침"
    elif (hour==12 and minu>=10) or (hour>=13 and hour<18) or (hour==18 and minu<10): Meal="점심"
    else:
        Meal="저녁"
        if (hour==6 and minu<50) or hour<=5 : Day=(Day+6)%7
    
    req=request.get_json() # 파라미터 값 불러오기
    userid=req["userRequest"]["user"]["properties"]["plusfriendUserKey"]
    stid="none"
    
    fr=open("/home/ubuntu/dg1s_bot/user data.txt","r") # 초기화
    lines=fr.readlines()
    fr.close()
    fw=open("/home/ubuntu/dg1s_bot/user data.txt","w")
    for line in lines:
        datas=line.split(" ")
        dusid=datas[0];
        if dusid==userid: stid=datas[1]
        if dusid!=userid: fw.write(line)
    fw.write(userid+" "+stid+" 7 none 0 none none\n")
    fw.close()
    
    res={
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            {
                                "title": "[저장 확인]",
                                "description": "학번    "+stid+"\n날짜    "+Days[Day]+"\n식사    "+Meal+"\n좌석    0",
                                "buttons": [
                                    { "action": "message", "label": "확인", "messageText": "확인했습니다." },
                                    { "action": "message", "label": "초기화", "messageText": "초기화" }
                                ]
                            },
                            { 
                                "thumbnail":{
                                    "imageUrl": "http://k.kakaocdn.net/dn/L689z/btqJ78BkcF5/oG7PgVEcPhCqma4ZwyvwAk/img_l.jpg", "fixedRatio": "true"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
    return jsonify(res)

@application.route('/excel', methods=['POST'])
def to_excel(): # 엑셀 파일로 생성
    
    wb=openpyxl.load_workbook('Gbob.xlsx',data_only=True) # 엑셀 기본 형식
    sh=wb['통계']
    j=0
    for sheet in wb:
        if not(sheet.title in classn): continue
        T=sheet.title; N=str(classN[j]+3)
        sh.cell(j+2,2).value=T
        sh.cell(j+2,3).value="=COUNTA("+T+"!D4:E"+N+","+T+"!G4:H"+N+","+T+"!J4:K"+N+","+T+"!M4:N"+N+","+T+"!P4:P"+N+")/((2*'통계'!$F$2-1)*("+N+"-3))"
        sh.cell(j+2,3).number_format="0.00%"
        #sheet['B3'].value="학번"; sheet['C3'].value="이름"; sheet['Q3'].value="참여율"
        #for k in range(4,17): 
        #    sheet.cell(2,k).value=Days[(k)//3][:1];
        #    if k%3==0: sheet.cell(3,k).value="아침"
        #    elif k%3==1: sheet.cell(3,k).value="점심"
        #    if k%3==2: sheet.cell(3,k).value="저녁"
        for k in range(4,4+classN[j]):
        #    if k-3<10: sheet.cell(k,2).value=classn[j]+"0"+str(k-3)
        #    else : sheet.cell(k,2).value=classn[j]+str(k-3)
            K=str(k)
            sheet.cell(k,17).value="=COUNTA(D"+K+":E"+K+",G"+K+":H"+K+",J"+K+":K"+K+",M"+K+":N"+K+",P"+K+")/(2*'통계'!$F$2-1)"
            sheet.cell(k,17).number_format="0%"
        j+=1

    fr=open("/home/ubuntu/dg1s_bot/final save.txt","r") # 엑셀 채워 넣기
    lines=fr.readlines()
    for line in lines:
        datas=line.split(" ")
        dstid=datas[0]; dday=int(datas[1]); dmeal=int(datas[2]); dseat=datas[3]
        col=dday*3+dmeal; row=int(dstid[2:])+3 
        if 4<=col and col<=16:
            sheet=wb[dstid[:2]]
            sheet.cell(row,col).value=dseat
    fr.close()
    
    wb.save("bob.xlsx")
    res={
        "version": "2.0",
        "template": {
            "outputs": [ { "simpleText": { "text": "Excel 파일 생성 완료" } } ]
        }
    }
    return jsonify(res)
    
@application.route('/menu', methods=['POST'])
def response_menu(): # 메뉴 대답 함수 made by 1316, 1301
    
    url = 'https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query=%EB%8C%80%EA%B5%AC%EC%9D%BC%EA%B3%BC%ED%95%99%EA%B3%A0%EB%93%B1%ED%95%99%EA%B5%90&oquery=eorndlfrhkrh+rmqtlr&tqi=U%2Ftz5wprvOssslHyxuossssssLN-415573'
    response = requests.get(url) # url로부터 가져오기
    if response.status_code == 200:    
        KST=timezone('Asia/Seoul') #현재 시간
        now=datetime.datetime.utcnow()
        day = int(utc.localize(now).astimezone(KST).strftime("%w"))   
        inputN = 6 # 평상시는 조/중/석/조/중/석 0 1 2 3 4 5
        if day == 1: inputN = 5 # 월요일은 중/석/조/중/석 () 1 2 3 4 5
        if day == 4: inputN = 5 # 목요일은 조/중/석/조/중 0 1 2 3 4 ()
        if day == 5: inputN = 2 # 금요일은 조/중 0 1 () () () ()
        i = 0
        pageN = 1; blockN = 1
        while i < inputN:       
            pathx = """#main_pack > section.sc_new.cs_school._cs_school > div > div.api_cs_wrap > div.school_area > div:nth-child(6) > div:nth-child("""
            pathy = """) > ul > li:nth-child("""
            pathz = """)"""
            pathc = pathx + str(pageN) + pathy + str(blockN) + pathz    
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            today0 = soup.select_one(pathc)
            today = today0.get_text() # 태그 없애고 텍스트만 추출
            tmenu = today.split() # 텍스트를 공백 기준으로 나눔
            del tmenu[0:3] # 앞에 3개(날짜 정보) 없앰
            tmenu = ' '.join(tmenu) # 다시 공백으로 붙임
            if day==1: Menu[(i+1)//3][(i+1)%3]=tmenu
            else : Menu[i//3][i%3]=tmenu
            i = i + 1
            if i == 1: pageN = 1; blockN = 2 
            elif i == 2: pageN = 2; blockN = 1
            elif i == 3: pageN = 2; blockN = 2
            elif i == 4: pageN = 3; blockN = 1
            elif i == 5: pageN = 3; blockN = 2
    
    req=request.get_json() # 파라미터 값 불러오기
    askmenu=req["action"]["detailParams"]["ask_menu"]["value"]
    msg=""
    now=datetime.datetime.utcnow()
    today=0
    hour=int(utc.localize(now).astimezone(KST).strftime("%H"))
    minu=int(utc.localize(now).astimezone(KST).strftime("%M"))
    if (hour==13 and minu<20) or (hour>=8 and hour<=12): Meal="아침" # 아침을 먹은 후
    elif (hour==13 and minu>=20) or (hour>=14 and hour<=18) or (hour==19 and minu<20): Meal="점심" # 점심을 먹은 후
    else: Meal="저녁" # 저녁을 먹은 후
    
    if Meal=="아침": fi=1; si=2; ti=0 # 아침 점심 저녁 정보 불러오기
    elif Meal=="점심": fi=2; si=0; ti=1
    elif Meal=="저녁": fi=0; si=1; ti=2
    if askmenu=="내일 급식": fi=0; si=1; ti=2; today=1;
    first=Menu[today][fi].replace(" ","\n") 
    second=Menu[today][si].replace(" ","\n")
    third=Menu[today][ti].replace(" ","\n")
    if Menu[today][fi]=="": first="등록된 급식이 없습니다."
    if Menu[today][si]=="": second="등록된 급식이 없습니다."
    if Menu[today][ti]=="": third="등록된 급식이 없습니다."
    
    res={ # 답변
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            { "title": Msg[today][fi], "description": first },
                            { "title": Msg[today][si], "description": second },
                            { "title": Msg[today][ti], "description": third }
                        ]
                    }
                }
            ]
        }
    }
    return jsonify(res)

@application.route('/')
def index():
    return render_template("index.html")
  
@application.route('/userdata')
def user_data(): # user data 사이트에서 보여주기
  
    data_send=""
    fr=open("/home/ubuntu/dg1s_bot/user data.txt","r")
    lines=fr.readlines()
    fr.close()
    for line in lines:
        data_send=data_send+line+"<br>"
    return jsonify(data_send)
  
@application.route('/ball')
def ball():
    return render_template("Ball.html")

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)

# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import os
import datetime
from datetime import timedelta
from pytz import timezone, utc
import openpyxl
import requests
from bs4 import BeautifulSoup

application=Flask(__name__)

# 참고 사항
# 변수명 앞에 d가 붙은 것은 저장된 데이터에서 불러온 값, d가 붙지 않은 것은 현재 or 입력한 데이터 값

KST=timezone('Asia/Seoul')
Days = ["일요일","월요일","화요일","수요일","목요일","금요일","토요일"] # 요일 이름
mday = [31,28,31,30,31,30,31,31,30,31,30,31] # 매월 일 수
Msg = [["[오늘 아침]","[오늘 점심]","[오늘 저녁]"],["[내일 아침]","[내일 점심]","[내일 저녁]"]] # 급식 title
Menu = [["","",""],["","",""]] # 오늘, 내일 급식
Menu_saved_date = "" # 급식 불러온 날짜
classn = ["11","12","13","14","21","22","23","24","31","32","33","34"] # 반 이름
classN = [20,20,20,21,20,19,19,19,14,13,10,11] # 반 학생 수
classtime = [["08:20","08:30"],["08:40","09:30"],["9:40","10:30"],["10:40","11:30"],["11:40","12:30"],["13:20","14:10"],["14:20","15:10"],["15:20","16:10"]]
Timetable = [[[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]]],
             [[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]]],
             [[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]],[[],[],[],[],[]]]]

# 시간표 변동사항 적는 곳
#

def prin(datas,classN): # 시간표 출력 함수
    
    now=datetime.datetime.utcnow() # 현재 시간
    day=int(utc.localize(now).astimezone(KST).strftime("%w"))
    title=""; answer=""
    subName=datas[0]; subZoomid=datas[1]; subZoompwd=datas[2] # datas: 0=name, 1=zoomid, 2=zoompwd, 3=hangout, 4=classroom, 5=teacher
    subHangout=datas[3]; subClassroom=datas[4]
    trimi=subName.find('(');
    if trimi!=-1: subName=subName[:trimi] # 과목명 출력할 때는 괄호 없애기
    
    if "반" in subName: # 조종례일 경우
        title+=Days[day]+" ["+subName
        if classN==0: title+=" 조례]"
        elif classN==8: title+=" 종례]"
    else : # 기타 과목
        title+=Days[day]+" "+str(classN)+"교시 : ["+subName+"]"
    
    if subName=="동아리": # 링크 첨부
        answer+="동아리 클래스룸을 참고하세요."
    if subZoomid!="none":
        answer+="줌 : https://zoom.us/j/"+subZoomid+"?pwd="+subZoompwd
    if subHangout!="none":
        answer+="행아웃 : https://meet.google.com/lookup/"+subHangout
    if subClassroom!="none":
        answer+="\n"+"클래스룸 : https://classroom.google.com/u/0/c/"+subClassroom
    if subZoomid=="none" and subHangout=="none" and subClassroom=="none":
        answer+="관련 접속 정보가 존재하지 않습니다."
    
    if classN!=8: title+=" ("+classtime[classN][0]+" ~ "+classtime[classN][1]+")" # 종례 제외 시간표시
    return title, answer

@application.route('/link', methods=['POST'])
def response_link(): # 온라인 시간표 대답 함수
    
    now = datetime.datetime.utcnow() # 현재 시간
    day = int(utc.localize(now).astimezone(KST).strftime("%w"))
    hour = int(utc.localize(now).astimezone(KST).strftime("%H"))
    minutes = int(utc.localize(now).astimezone(KST).strftime("%M"))
    classN = 0
    # 기본 : 시작시간 - 20 ~ 종료시간 - 10
    # 예외 : 조례, 종례, 5교시(점심시간)
    if (3 <= hour <= 7) or (hour == 8 and minutes < 23): classN = 0 # 8:20~8:30
    elif ((hour == 8 and minutes >= 23) or (hour == 9 and minutes < 20)): classN = 1 # 8:40~9:30
    elif ((hour == 9 and minutes >= 20) or (hour == 10 and minutes < 20)): classN = 2 # 9:40~10:30
    elif ((hour == 10 and minutes >= 20) or (hour == 11 and minutes < 20)): classN = 3 # 10:40~11:30
    elif ((hour == 11 and minutes >= 20) or (hour == 12 and minutes < 20)): classN = 4 # 11:40~12:30
    elif (hour == 12 and minutes >= 20) or (hour == 13): classN = 5 # 13:20~14:10
    elif (hour == 14): classN = 6 # 14:20~15:10
    elif (hour == 15): classN = 7 # 15:20~16:10
    elif (hour == 16 and minutes <= 20): classN = 8 # 16:10~16:20
    else : classN = 9 # 수업 없음
        
    req=request.get_json() # 파라미터 값 불러오기
    userid=req["userRequest"]["user"]["properties"]["plusfriendUserKey"]
    stid="none"
    fr=open("/home/ubuntu/dg1s_bot/user data.txt","r") # 학번 불러오기
    lines=fr.readlines()
    for line in lines:
        datas=line.split(" ")
        dusid=datas[0]; dstid=datas[1];
        if dusid==userid: stid=dstid
    fr.close()
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
        if day==6 or day==0 :#or classN==9: # 수업이 없는 경우
            res={
                "version": "2.0",
                "template": { "outputs": [ { "simpleText": { "text": "진행 중인 수업이 없습니다." } } ] }
            }
            return jsonify(res)
        else :
            grade=int(stid[0]); classn=int(stid[1])
            items=[]
            fr=open("/home/ubuntu/dg1s_bot/timetable.txt","r")
            lines=fr.readlines()
            for j in range(3):
                for k in range(4):
                    for l in range(5):
                        global Timetable
                        line=lines[26*j+2+6*k+l].split(" ")
                        Timetable[j][k][l]=[]
                        for sub in line:
                            sub=sub.replace("\n","")
                            Timetable[j][k][l].append(sub)
            fr.close()
            for i in range(9): # 해당 요일의 시간표 모두 출력  
                subjectName=Timetable[grade-1][classn-1][day-1][(classN+i)%9]
                fr=open("/home/ubuntu/dg1s_bot/subject data.txt","r")
                lines=fr.readlines()
                isgrade=False # 과목명이 겹칠 경우를 대비해 해당 학년의 과목명이 맞는지 확인하기 위한 변수
                for line in lines:
                    datas=line.split(" ")
                    dname=datas[0];
                    if dname==str(grade)+"학년\n":
                        isgrade=True; continue
                    if isgrade==True and "학년" in dname: break
                    if isgrade==True and dname==subjectName: 
                        title, answer=prin(datas,(classN+i)%9)
                        item={ "title": title, "description": answer }
                        items.append(item)
                        break
                fr.close()
            res={ # 답변
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "carousel": {
                                "type": "basicCard",
                                "items": items
                            }
                        },
                        {
                            "simpleText":{
                                "text": "* 실제 시간표는 위와 다를 수 있다는 점 유의하시기 바랍니다."
                            }
                        }
                    ]
                }
            }
            return jsonify(res)

def what_is_menu():
    
    global Menu, Menu_saved_date
    now = datetime.datetime.utcnow() # 오늘, 내일 날짜
    today = utc.localize(now).astimezone(KST)
    tomorrow = today + timedelta(days=1)
    today_name = " "+str(today.month)+"월 "+str(today.day)+"일 " # 추후 비교용 날짜명 텍스트("_N월_N일_")
    tomorrow_name = " "+str(tomorrow.month)+"월 "+str(tomorrow.day)+"일 "
    
    if Menu_saved_date == "" or Menu_saved_date != today_name :
      Menu_saved_date = today_name
      
      url = 'https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query=%EB%8C%80%EA%B5%AC%EC%9D%BC%EA%B3%BC%ED%95%99%EA%B3%A0%EB%93%B1%ED%95%99%EA%B5%90&oquery=eorndlfrhkrh+rmqtlr&tqi=U%2Ftz5wprvOssslHyxuossssssLN-415573'
      response = requests.get(url) # url로부터 가져오기
      if response.status_code == 200:  
          
          source = response.text # menu_info class 내용 가져오기
          soup = BeautifulSoup(source,'html.parser')
          a = soup.select('.menu_info')
          
          for menu in a:
              menu_text = menu.get_text()
              bracket_i = menu_text.find('[')
              bracket_j = menu_text.find(']')
              menu_day = menu_text[:bracket_i]
              menu_when = menu_text[bracket_i+1:bracket_j]
              menu_content = menu_text[bracket_j+3:].rstrip().replace(" ","\n")
              
              if menu_when == "조식": save_i = 0
              elif menu_when == "중식": save_i = 1
              elif menu_when == "석식": save_i = 2
              
              if menu_day == today_name: Menu[0][save_i]=menu_content
              elif menu_day == tomorrow_name: Menu[1][save_i]=menu_content
    
    req=request.get_json() # 파라미터 값 불러오기
    askmenu=req["action"]["detailParams"]["ask_menu"]["value"]
    
    hour=int(utc.localize(now).astimezone(KST).strftime("%H")) # Meal 계산
    minu=int(utc.localize(now).astimezone(KST).strftime("%M"))
    if (hour==13 and minu<20) or (hour>=8 and hour<=12): Meal="아침" # 아침을 먹은 후
    elif (hour==13 and minu>=20) or (hour>=14 and hour<=18) or (hour==19 and minu<20): Meal="점심" # 점심을 먹은 후
    else: Meal="저녁" # 저녁을 먹은 후
    
    i = 0
    
    if Meal == "아침": fi=1; si=2; ti=0 # 아침 점심 저녁 정보 불러오기 및 배열
    elif Meal == "점심": fi=2; si=0; ti=1
    elif Meal == "저녁": fi=0; si=1; ti=2
    if askmenu == "내일 급식": fi=0; si=1; ti=2; i=1
    first = Menu[i][fi]
    second = Menu[i][si]
    third = Menu[i][ti]
    if Menu[i][fi] == "": first = "등록된 급식이 없습니다."
    if Menu[i][si] == "": second = "등록된 급식이 없습니다."
    if Menu[i][ti] == "": third = "등록된 급식이 없습니다."
    return Msg[i][fi], Msg[i][si], Msg[i][ti], first, second, third

@application.route('/menu', methods=['POST'])
def response_menu(): # 메뉴 대답 함수 made by 1316, 1301
    
    msg1, msg2, msg3, menu1, menu2, menu3 = what_is_menu()
    res={ # 답변
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            { "title": msg1, "description": menu1 },
                            { "title": msg2, "description": menu2 },
                            { "title": msg3, "description": menu3 }
                        ]
                    }
                }
            ]
        }
    }
    return jsonify(res)

@application.route('/seat', methods=['POST'])
def input_seat(): # 좌석 번호 입력 함수
    
    now=datetime.datetime.utcnow()
    Day=int(utc.localize(now).astimezone(KST).strftime("%w"))
    hour=int(utc.localize(now).astimezone(KST).strftime("%H"))
    minu=int(utc.localize(now).astimezone(KST).strftime("%M"))
    date=int(utc.localize(now).astimezone(KST).strftime("%d"))
    month=int(utc.localize(now).astimezone(KST).strftime("%m"))
    year=int(utc.localize(now).astimezone(KST).strftime("%Y"))
    if (hour==6 and minu>=50) or (hour>=7 and hour<12) or (hour==12 and minu<10): Meal="아침" # 가장 최근 식사가 언제인지 자동 계산
    elif (hour==12 and minu>=10) or (hour>=13 and hour<18) or (hour==18 and minu<10): Meal="점심"
    else:
        Meal="저녁"
        if (hour==6 and minu<50) or hour<=5 : Day=(Day+6)%7
        
    req=request.get_json() # 파라미터 값 불러오기
    userid=req["userRequest"]["user"]["properties"]["plusfriendUserKey"]
    day=req["action"]["detailParams"]["sys_date"]["value"] # 형식: {"date": "2021-02-09", "dateTag": "today", "dateHeadword": null, "year": null, "month": null, "day": null}
    meal=req["action"]["detailParams"]["seat_menu"]["value"]
    seat=int(req["action"]["detailParams"]["table_seat"]["value"])
    p1=req["action"]["detailParams"]["student_id"]["value"] # 같이 앉은 사람
    p2=req["action"]["detailParams"]["student_id1"]["value"] # 같이 앉은 사람
    stid="none"; invt=False; cday=0; ciday=0

    if day!="7": # 유효한 날짜값인지 계산(유효한 날짜값: 이번주 월~오늘)
        if day.split('"')[3]=="dateTag": invt=True # 1~9998년이 아닌 경우
        else :
            iyear=int(day.split('"')[3][:4]) # 입력한 날짜와 현재 날짜가 1년 1월 1일부터 몇일째인지 계산
            imonth=int(day.split('"')[3][5:7])
            idate=int(day.split('"')[3][8:])
            cday=(year-1)*365+(year-1)//4-(year-1)//100+(year-1)//400;
            ciday=(iyear-1)*365+(iyear-1)//4-(iyear-1)//100+(iyear-1)//400;
            if (year%4==0 and year%100!=0) or year%400==0: cday+=1
            if (iyear%4==0 and iyear%100!=0) or iyear%400==0: ciday+=1
            for i in range(0,month-1): cday+=mday[i]
            for i in range(0,imonth-1): ciday+=mday[i]
            cday+=date; ciday+=idate
            if (hour==6 and minu<50) or hour<=5 : cday-=1

            if cday-ciday>=0 and cday-ciday<=Day-1 : invt=False
            else : invt=True
            day=ciday%7
    if meal!="none" and cday==ciday: # 유효한 식사인지 계산
        if Meal=="아침" and meal!="아침": invt=True
        elif Meal=="점심" and meal=="저녁": invt=True
    
            
    if invt==True: #유효하지 않은 날짜값
        if Day==0 or Day==6:
            res={
                "version": "2.0",
                "template": { "outputs": [ { "simpleText": { "text": "오늘은 주말이므로 좌석 번호 기록이 없습니다." } } ] }
            }
        else :
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
            dusid=datas[0]; dstid=datas[1]; dday=datas[2]; dmeal=datas[3] # data 불러오기
            dseat=int(datas[4]); dp1=datas[5]; dp2=datas[6].rstrip()
            if dusid==userid:
                stid=dstid
                if dday!="7" and day=="7": day=int(dday) # 요일
                if dday=="7" and day=="7": day=Day
                if dmeal!="none" and meal=="none": meal=dmeal # 식사
                if dmeal=="none" and meal=="none": meal=Meal
                if seat==0: seat=dseat # 좌석 
                if p1=="none" and p2=="none": # 같이 앉은 사람
                    p1=dp1; p2=dp2
                elif p1!="none" and p2=="none": # 항상 p1이 p2보다 우선적으로 채워지도록
                    if dp1=="none" and dp2=="none": p1=p1; p2=dp2
                    elif dp1!="none" and dp2=="none": p2=p1; p1=dp1
                    elif dp1!="none" and dp2!="none": p2=p1; p1=dp2
            else : fw.write(line)
        if day=="7": day=Day
        if meal=="none": meal=Meal
        if p2==stid or p2==p1: p2="none" # 입력한 사람이 자기 자신이거나 중복일 경우
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
        else: # 
            stids=stid
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
    
    wb = openpyxl.load_workbook('Gbob.xlsx',data_only=True) # 엑셀 기본 형식
    sh = wb['통계']
    j = 0
    for sheet in wb:
        if not(sheet.title in classn): continue
        T = sheet.title; N = str(classN[j]+3)
        # 통계 칸 채우기
        sh.cell(j+2,4).value = "=COUNTA("+T+"!D4:E"+N+","+T+"!G4:H"+N+","+T+"!J4:K"+N+","+T+"!M4:N"+N+","+T+"!P4:P"+N+")/('통계'!$F$2*("+N+"-3))"
        sh.cell(j+2,4).number_format = "0.00%"
        #sheet['B3'].value="학번"; sheet['C3'].value="이름"; sheet['Q3'].value="참여율"
        #for k in range(4,17): 
        #    sheet.cell(2,k).value=Days[(k)//3][:1];
        #    if k%3==0: sheet.cell(3,k).value="아침"
        #    elif k%3==1: sheet.cell(3,k).value="점심"
        #    if k%3==2: sheet.cell(3,k).value="저녁"
        for k in range(4,4+classN[j]):
        #    if k-3<10: sheet.cell(k,2).value=classn[j]+"0"+str(k-3)
        #    else : sheet.cell(k,2).value=classn[j]+str(k-3)
            # 참여율 칸 채우기
            K = str(k)
            sheet.cell(k,17).value = "=COUNTA(D"+K+":E"+K+",G"+K+":H"+K+",J"+K+":K"+K+",M"+K+":N"+K+",P"+K+")/'통계'!$F$2"
            sheet.cell(k,17).number_format = "0%"
        j += 1

    fr=open("/home/ubuntu/dg1s_bot/final save.txt","r") # 엑셀 채워 넣기
    lines=fr.readlines()
    for line in lines:
        if " 7 " in line or "none" in line: continue
        datas=line.split(" ")
        if len(datas)!=5: continue
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

@application.route('/upst', methods=['POST'])
def update_stid(): # 학번 갱신 함수
    
    updatestr="" # 형식: "이전 학번_새 학번_..." ex) "1301 2301 1316 2316" 
    
    fr=open("/home/ubuntu/dg1s_bot/user data.txt","r")
    lines=fr.readlines()
    fr.close()
    fw=open("/home/ubuntu/dg1s_bot/user data.txt","w")
    for line in lines:
        former_stid=line.split(" ")[1]
        i=updatestr.find(former_stid)
        if i!=-1: 
            new_stid=updatestr[i+5:i+9]
            line=line.replace(former_stid,new_stid)
        fw.write(line)
    fw.close()
    
    res={
        "version": "2.0",
        "template": {
            "outputs": [ { "simpleText": { "text": "학번 갱신 완료" } } ]
        }
    }
    return jsonify(res)
 
@application.route('/')
def index():
    return render_template("index.html")

filename=""

@application.route('/texteditor')
def text_editor(): # 원하는 파일 사이트에서 보여주고 편집
    global filename
    filename=request.args.get('filename')
    fr=open("/home/ubuntu/dg1s_bot/"+filename+".txt","r")
    data_send=fr.readlines()
    fr.close()
    if filename=="user data": data_send.sort(key=lambda x:x[13:17]) # 학번 순 정렬
    return render_template("texteditor.html",data=data_send, name=filename)

@application.route('/filesave', methods=['GET','POST'])
def save_as_file(): # txt file 저장하기
    if request.method=='POST':
        text=request.form['content']
        text=str(text)
        with open("/home/ubuntu/dg1s_bot/"+filename+".txt","w",encoding='utf-8') as f:
            f.write(text)
        return render_template("saved.html")
  
@application.route('/xlsave', methods=['GET','POST'])
def save_as_xlfile(): # file 저장하기
    if request.method == 'POST':
        f=request.files['xlfile']
        f.save("/home/ubuntu/dg1s_bot/"+secure_filename(f.filename))
        return render_template("saved.html")
  
@application.route('/dnldfile', methods=['GET','POST'])
def download_file(): # file 다운받기
    if request.method == 'POST':
        filename=request.form['downloadfilename']
        return send_file("/home/ubuntu/dg1s_bot/"+filename, attachment_filename=filename, as_attachment=True)

@application.route('/file')
def upload_n_download():
    files=os.listdir("/home/ubuntu/dg1s_bot")
    folders=[]
    for file in files:
        if not '.' in file: folders.append(file)
    for folder in folders:
        files.remove(folder)
    return render_template("file.html", files=files)
  
@application.route('/ball')
def ball():
    return render_template("Ball.html")

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)

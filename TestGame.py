import sys
import time
import json
import getpass
import codecs
import traceback
from PTTLibrary import PTT

from uao import Big5UAOCodec
uao = Big5UAOCodec()

# 如果你想要自動登入，建立 Account.txt
# 然後裡面填上 {"ID":"YourID", "Password":"YourPW"}

BoardList = ['Wanted', 'Gossiping', 'Test', 'NBA', 'Baseball', 'LOL', 'C_Chat']

PTTBot = None
ResPath = './OldBug/'

def showPost(Post):
    PTTBot.Log('文章代碼: ' + Post.getID())
    PTTBot.Log('作者: ' + Post.getAuthor())
    PTTBot.Log('時間: ' + Post.getDate())
    PTTBot.Log('標題: ' + Post.getTitle())
    PTTBot.Log('價錢: ' + str(Post.getMoney()))
    PTTBot.Log('IP: ' + Post.getIP())
    PTTBot.Log('網址: ' + Post.getWebUrl())

    # PTTBot.Log('內文: ' + Post.getContent())

    PushCount = 0
    BooCount = 0
    ArrowCount = 0
    ERCount = 0
    ORCount = 0

    # open('Big5Data.txt',"wb").write(Post.getRawData())

    for Push in Post.getPushList():
        if Push.getType() == PTT.PushType.Push:
            PushCount += 1
        elif Push.getType() == PTT.PushType.Boo:
            BooCount += 1
        elif Push.getType() == PTT.PushType.Arrow:
            ArrowCount += 1
        elif Push.getType() == PTT.PushType.EditRecord:
            ERCount += 1
        elif Push.getType() == PTT.PushType.OtherRecord:
            ORCount += 1
        
        Author = Push.getAuthor()
        Content = Push.getContent()
        
        # print(str(Push.getLineNumber()) + ') ' + Author + ': ' + Content)
        
    PTTBot.Log('共有 ' + str(PushCount) + ' 推 ' + str(BooCount) + ' 噓 ' + str(ArrowCount) + ' 箭頭 ' + str(ERCount) + ' 編輯紀錄 ' + str(ORCount) + ' 其他紀錄 ')

def GetPostDemo():
    
    # 這個範例是如何取得單一文章資訊
    # getPost
    # 第一個固定參數是板面
    # 第二個參數就是你想查詢的文章編號或者文章代碼
        
    #回傳值 錯誤碼, 文章資訊
    
    #文章資訊的資料結構可參考如下
    
    ################## 文章資訊 Post information ##################
    # getBoard                  文章所在版面
    # getID                     文章 ID ex: 1PCBfel1
    # getAuthor                 作者
    # getDate                   文章發布時間
    # getTitle                  文章標題
    # getContent                文章內文
    # getMoney                  文章P幣
    # getWebUrl                 文章網址
    # getPushList               文章即時推文清單
    
    ################## 推文資訊 Push information ##################
    # getType                   推文類別 推噓箭頭
    # getAuthor                 推文ID
    # getContent                推文內文
    # getTime                   推文時間
    
    ErrCode, Post = PTTBot.getPost('Test', PostIndex=500, LineNumber=0)
    showPost(Post)

def GameDemo():
    Board = 'Test' # 板名。請自行添增此兩參數
    PostIndex = 500 # 文章編號
    
    Response = []
    
    CheckedLN = 0
    NotFinished = True

    PTTBot.editArticle(Board, '\rStart!!!\r\r1+1=?\r\r', PostIndex=500)

    JustEdit = True
    
    while NotFinished:

        time.sleep(5) # 慢點兒
        
        ErrCode, Post = PTTBot.getPost('@'+Board, PostIndex=PostIndex, LineNumber=CheckedLN) # @記號代表此時已位於文章前
        if ErrCode != PTT.ErrorCode.Success:
            PTTBot.Log('使用文章編號取得文章詳細資訊失敗 錯誤碼: ' + str(ErrCode))
        
        PList = Post.getPushList()
        
        if JustEdit:
            EditRecordLine = [x.getLineNumber() for x in PList if x.getType() == PTT.PushType.EditRecord]
            JustEdit = False

        if len(PList)>0: 
            CheckedLN = PList[-1].getLineNumber()
        PTTBot.Log('已檢查過 ' + str(CheckedLN) + '行')
        
        if Response == []: # 防止偷跑，掃過一輪再給答案
            Response = ['**2', '\rRight!\r\rAns+Ans = ?\r']
            continue
        
        for Push in PList:
            if Response[0] in Push.getContent():
                
                PTTBot.editArticle('@'+Board, [Response[1]]+ [None]*len(EditRecordLine), LineNumber=[Push.getLineNumber()] + EditRecordLine) # 編輯文章
                CheckedLN = Push.getLineNumber() - len(EditRecordLine)
                JustEdit = True
                Response[0] = '**' + str(int(Response[0][2:])*2)
                break
                
            elif 'END' in Push.getContent():
                NotFinished = False
    
if __name__ == '__main__':
    print('Welcome to PTT Library v ' + PTT.Version + ' Demo')

    if len(sys.argv) == 2:
        if sys.argv[1] == '-ci':
            print('CI test run success!!')
            sys.exit()

    try:
        with open('Account.txt') as AccountFile:
            Account = json.load(AccountFile)
            ID = Account['ID']
            Password = Account['Password']
    except FileNotFoundError:
        ID = input('請輸入帳號: ')
        Password = getpass.getpass('請輸入密碼: ')
    
    # 不會把重複的登入踢掉，設定 Log level 為 除錯等級
    # PTTBot = PTT.Library(ID, Password, kickOtherLogin=False, _LogLevel=PTT.LogLevel.DEBUG)
    # 水球接收器，不過沒長時間測試，大量API呼叫的時候可能不穩
    # PTTBot = PTT.Library(ID, Password, WaterBallHandler=WaterBallHandler)
    # PTTBot = PTT.Library(ID, Password, _LogLevel=PTT.LogLevel.DEBUG)
    # Log 接收器，如果有需要把內部顯示抓出來的需求可以用這個
    # PTTBot = PTT.Library(ID, Password, LogHandler=LogHandler)
    PTTBot = PTT.Library(ID, Password, kickOtherLogin=False, _LogLevel=PTT.LogLevel.DEBUG)

    ErrCode = PTTBot.login()
    if ErrCode != PTT.ErrorCode.Success:
        PTTBot.Log('登入失敗')
        sys.exit()
    
    try:
        # GetPostDemo()
        GameDemo()
        pass
    except Exception as e:
        
        traceback.print_tb(e.__traceback__)
        print(e)
        PTTBot.Log('接到例外 啟動緊急應變措施')
    # 請養成登出好習慣
    PTTBot.logout()
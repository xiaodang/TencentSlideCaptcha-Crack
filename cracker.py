# coding=utf-8

from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import cv2
import numpy as np
from io import BytesIO
import time, requests


START_DISTANCE=(22 + 16) * 2
DEBUG=False
chromedriver = "/Users/xiaoye/Documents/software/chromedriver" 


class CrackSlider():
    """
    通过浏览器截图，识别验证码中缺口位置，获取需要滑动距离，并模仿人类行为破解滑动验证码
    这里使用网易易盾滑动模块http://dun.163.com/trial/jigsaw
    过程参考https://www.jianshu.com/p/f12679a63b8d
    目前进度：已完成本地测试，代码待优化。
    """
    def __init__(self):
        self.url = 'https://007.qq.com/online.html'
        self.driver = webdriver.Chrome(chromedriver)
        self.wait = WebDriverWait(self.driver, 20) #等待页面元素的加载
        self.bgWrapWidth=341
        self.target_img=None
    
    # 打开网址
    def openTest(self):
        self.driver.get(self.url)
        self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/section[1]/div/div/div/div[2]/div[1]/a[2]'))).click()
        self.wait.until(EC.presence_of_element_located((By.ID, 'code'))).click()
        self.wait.until(EC.presence_of_element_located((By.ID, 'tcaptcha_iframe')))
        time.sleep(2)
        self.driver.switch_to_frame('tcaptcha_iframe')


    def get_pic(self):
        target = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="slideBg"]'))) # 背景图片
        # template = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="slideBlock"]'))) # 滑动图片
        self.bgWrapWidth=target.size['width']
        time.sleep(2)
        target_link =target.get_attribute('src')
        # template_link = template.get_attribute('src')
        self.target_img=Image.open(BytesIO(requests.get(target_link).content))
        # template_img = Image.open(BytesIO(requests.get(template_link).content))
        if(DEBUG):
            img_name='%s.jpg' % (str(int(time.time())))
            target_img.save(img_name)
        # template_img.save('template.png')
        # local_img = Image.open('target.jpg')

    # 参数：要移动的总距离
    def get_tracks(self, distance):
        tracks=[]
        step=3
        for i in range(int(distance/step)):
            tracks.append({"x":step,"y":0,'sleep':0})
        tracks.append({"x":distance-step*len(tracks),"y":0,'sleep':0})        
        return tracks

    def matchGray(self):
        # bufferImg=np.array(Image.open('1586260669.jpg').convert('RGB'))
        bufferImg=np.array(self.target_img)
        grayImg = cv2.cvtColor(bufferImg, cv2.COLOR_BGR2GRAY)
        blackImg=grayImg<125
        whiteImg=grayImg>230
        width=blackImg.shape[1]
        height=blackImg.shape[0]
        for w in range(340,width-18):
            whiteLineLen=0
            for h in range(0,height):
                widthnum=min(width-w,28)
                if np.sum(blackImg[h,w:w+widthnum])/float(widthnum)>0.8 and whiteImg[h][w]:
                    whiteLineLen=whiteLineLen+1
                # print(u'width:heidht %s:%s,白色像素数:%s' % (str(w),str(h),str(whiteLineLen)))                
                if(whiteLineLen>=50):
                    distance=int((w-START_DISTANCE)/(width/float(self.bgWrapWidth)))
                    print(u'gap width,',w,u'should move distance:',distance)
                    return distance

    def refreshCapatch(self):
        self.wait.until(EC.presence_of_element_located((By.ID, 'reload'))).click()
        pass

    def isBlack(self,fullRgb):
        return fullRgb[0] * 0.3 + fullRgb[1] * 0.6 + fullRgb[2] * 0.1 <= 125
    
    def isWhite(self,fullRgb):
        return (abs(fullRgb[0] - 0xff) + abs(fullRgb[1] - 0xff) + abs(fullRgb[2] - 0xff)) < 125

    def crack_slider(self,tracks):
        slider = self.wait.until(EC.element_to_be_clickable((By.ID, 'tcaptcha_drag_thumb')))
        ActionChains(self.driver).click_and_hold(slider).perform()
        # 前进
        d=0
        for track in tracks:
            ActionChains(self.driver).move_by_offset(xoffset=track['x'], yoffset=track['y']).perform()
            d=d+track['x']
            print('move to right distance:%s pixel' % (d))
            # 停顿0.1 秒
            # time.sleep(track['sleep'])
        # 释放滑块
        ActionChains(self.driver).release().perform()

    def validCapatch(self):
        # 得到图像以及缩放比
        self.get_pic()
        # 得到缺块的位置
        distance = self.matchGray()
        #计算失败 重试
        if not distance:
            self.refreshCapatch()
            distance = self.matchGray()
        tracks = self.get_tracks(distance)  # 对位移的缩放计算
        self.crack_slider(tracks)

def run():
    cs = CrackSlider()
    cs.openTest()
    cs.validCapatch()
    time.sleep(5)

if __name__ == '__main__':
    run()
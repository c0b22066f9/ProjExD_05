import math
import random
import sys
import time

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"


    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]

        

            if self.state == "normal" or self.hyper_life < 0:
                self.state = "normal"
                self.image = self.imgs[self.dire]
            elif self.state == "hyper":
                self.image = pg.transform.laplacian(self.imgs[self.dire])  # 画像imageを変換
                self.hyper_life -= 1  # 発動時間hyper_lifeを1減らす
            
        screen.blit(self.image, self.rect)

    def get_direction(self) -> tuple[int, int]:
        return self.dire
    
    def change_state(self, state: str, hyper_life: int):
        """
        追加機能3
        引数1 state：状態（"hyper"と"normal"）
        引数2 hyper_life：発動時間
        """
        self.state = state
        self.hyper_life = hyper_life

class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery + emy.rect.height/2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex05/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"ex05/fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class Shield(pg.sprite.Sprite):
    """
    防御壁に関するクラス
    引数1 bird:防御壁
    引数2 life:防御壁の発動時間
    """
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        self.vx , self.vy = bird.get_direction()
        theta = math.atan2(-self.vy, self.vx) #こうかとんの向き (弧度法)
        angle = math.degrees(theta) #こうかとんの向き (度数法)
        self.image = pg.Surface((20, bird.rect.height*2))
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)
        pg.draw.rect(self.image, (0, 0, 0), pg.Rect(0, 0, 20, bird.rect.height*2))
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.life = life
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
       
    def update(self):
        """
        爆発時間を1減算し、発動時間中は防御壁矩形を有効化
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def score_up(self, add):
        self.score += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)


class NeoGravity(pg.sprite.Sprite):
    def __init__(self, life: int):
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (10, 10, 10), pg.Rect(0, 0, WIDTH, HEIGHT))
        self.image.set_colorkey((0, 0, 0))
        self.image.set_alpha(200)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH/2, HEIGHT/2
        self.life = life
        
    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()
        
class Gravity(pg.sprite.Sprite):
    def __init__(self, bird, life):
        super().__init__()
        rad = 200
        self.life = life
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, (1, 1, 1), (rad, rad), rad)
        self.rect = self.image.get_rect()
        self.image.set_colorkey("black")
        self.image.set_alpha(127) #黒を透明化
        self.rect.center = bird.rect.center #self.rectがこうかとんを追う

    def update(self, bird):
        self.rect.center = bird.rect.center
        self.life = self.life - 1
        if self.life <= 0:
            self.kill()
        

class FrontKoukaShield(pg.sprite.Sprite):
    """
    こうかとんの前に防御壁を作るクラス
    引数1 bird 防御壁
    引数2 life 防御壁の発動秒数
    """
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        self.life = life
        theta = math.atan2(-self.vy, self.vx) #こうかとんの向き(弧度法)
        angle = math.degrees(theta) #こうかとんの向き(度数法)
        self.image = pg.Surface((20, bird.rect.height * 2))
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)
        pg.draw.rect(self.image, (255, 0, 0), pg.Rect(0, 0, 20, bird.rect.height * 2))
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + bird.rect.width*self.vx  # self.rect.centerxがこうかとんを追う
        self.rect.centery = bird.rect.centery + bird.rect.height*self.vy  # self.rect.centeryがこうかとんを追う
        # 爆弾を落下するemyから見た攻撃対象のbirdの方向を計算

    def update(self, bird: Bird):
        """
        防御壁の発動秒数を１減算し、発動中はこうかとんの前に防御壁を有効化
        """
        self.rect.centerx = bird.rect.centerx + bird.rect.width*self.vx
        self.rect.centery = bird.rect.centery + bird.rect.height*self.vy
        self.life -= 1
        if self.life < 0:
            self.kill()


class BackKoukaShield(pg.sprite.Sprite):
    """
    こうかとんの後ろに防御壁を作るクラス
    引数1 bird 防御壁
    引数2 life 防御壁の発動秒数
    """
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        self.life = life
        rev_theta = math.atan2(-self.vy, -self.vx)
        angle2 = math.degrees(rev_theta)
        self.image = pg.Surface((20, bird.rect.height*2))
        self.image = pg.transform.rotozoom(self.image, angle2, 1.0)
        pg.draw.rect(self.image, (255, 255, 0), pg.Rect(0, 0, 20,bird.rect.height * 2))
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + bird.rect.width*(-self.vx)  # self.rect.centerxがこうかとんを追う
        self.rect.centery = bird.rect.centery + bird.rect.height*(-self.vy)  # self.rect.centeryがこうかとんを追う

    def update(self, bird: Bird):
        """
        防御壁の発動時間を1減算、発動中はこうかとんの後ろに防御壁を展開
        """
        self.rect.centerx = bird.rect.centerx + bird.rect.width*(-self.vx)
        self.rect.centery = bird.rect.centery + bird.rect.height*(-self.vy)
        self.life -= 1
        if self.life < 0:
            self.kill()

class DethBall(pg.sprite.Sprite):
    def __init__(self, bird: Bird):
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        rad = 100
        self.image = pg.Surface((2*rad, 2*rad))
        color = self.image.fill("white")
        
        # 白を消す処理を入れる
        self.image.set_alpha(127)
        pg.draw.circle(self.image,"purple", (rad, rad), rad)
        self.image.set_colorkey("white")
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()
class GoldenKoukaton(pg.sprite.Sprite):
    """
    こうかとんをゴールデンこうかとんに変身させるクラス
    """
    def __init__(self, bird, life):
        super().__init__()
        rad = 100
        self.life = life
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, (1, 1, 1), (rad, rad), rad)
        self.rect = self.image.get_rect()
        self.image.fill("gold")
        self.image.set_alpha(127) #透明化

        self.rect.center = bird.rect.center  #self.rectがこうかとんを追う

    def update(self, bird):
        self.rect.center = bird.rect.center
        self.life = self.life - 1
        if self.life <= 0:
            self.kill()

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    neogrs = pg.sprite.Group()
    gravities = pg.sprite.Group()

    score.score = 20000

    shields = pg.sprite.Group()
    
    FrontKS = pg.sprite.Group()
    BackKS = pg.sprite.Group()
    GolKk = pg.sprite.Group()
    Db = pg.sprite.Group()
    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:  # 左シフトが押されているか判定
                bird.speed = 20  # スピードアップ
            if event.type == pg.KEYUP and event.key == pg.K_LSHIFT:  # 左シフトが押された状態から離れたら
                bird.speed = 10  #もとのスピードに戻る
            if event.type == pg.KEYDOWN and event.key ==pg.K_RETURN:
                if score.score > 200:
                    neogrs.add(NeoGravity(400))
                    score.score_up(-200)
            # 追加機能3
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.score > 100:  #→Shiftキー押下、かつスコアが100より大きいとき
                score.score -= 100
                bird.change_state("hyper", 500)

            if event.type == pg.KEYDOWN and event.key == pg.K_TAB and score.score > 50:
                #矢印キーとtabキーが押されて、スコアが50以上ならスコアを-50する.
                gravities.add(Gravity(bird, 500))
                score.score -= 50

            if event.type ==pg.KEYDOWN and event.key == pg.K_CAPSLOCK and len(shields) == 0 :
                if score.score > 50:
                    score.score_up(-50)
                    shields.add(Shield(bird, 400))
                   
            if event.type == pg.KEYDOWN and event.key == pg.K_x and len(FrontKS) == 0 : 
                if score.score > 50:
                    score.score_up(-50)
                    FrontKS.add(FrontKoukaShield(bird, 400))
                    BackKS.add(BackKoukaShield(bird, 400))
            if event.type == pg.KEYDOWN and event.key == pg.K_f and score.score > 50:

                GolKk.add(GoldenKoukaton(bird, 500))
                score.score -= 50
                if event.type == pg.KEYDOWN and event.key == pg.K_d:
                    Db.add(DethBall(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_d and score.score > 70:
                Db.add(DethBall(bird))
                score.score -= 70
        screen.blit(bg_img, [0, 0])


        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())
        
        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

           
        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bird.state == "normal":
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            elif bird.state == "hyper":
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.score_up(1)  # 1点アップ


        for emy in pg.sprite.groupcollide(emys, gravities, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        # for bomb in pg.sprite.groupcollide(bombs, gravities, True, False).keys():

        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
 
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for bomb in pg.sprite.groupcollide(bombs, FrontKS, True, False).keys():

            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ
        
        for bomb in pg.sprite.groupcollide(bombs, BackKS, True, False).keys():

            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for emy in pg.sprite.groupcollide(emys, Db, True, False).keys():
            exps.add(Explosion(emy, 50))
            score.score_up(10)
        for bomb in pg.sprite.groupcollide(bombs, Db, True, False).keys():
            exps.add(Explosion(bomb, 50))
            score.score_up(1)
        
        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        for bomb in pg.sprite.groupcollide(bombs, neogrs, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ
            
        for emy in pg.sprite.groupcollide(emys, neogrs, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト


        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        neogrs.update()
        neogrs.draw(screen)
        score.update(screen)
        gravities.update(bird)
        gravities.draw(screen)

        shields.update()
        shields.draw(screen)
        FrontKS.update(bird)
        FrontKS.draw(screen)
        BackKS.update(bird)
        BackKS.draw(screen)
        GolKk.update(bird)
        GolKk.draw(screen)
        Db.update()
        Db.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit
    sys.exit()


"""
SHADOW-BOXER  –  Shadow Fight 4 Edition
========================================
Keyboard:
  A / D / ←/→  – Move          Q – Punch (standing)
  W / Space    – Jump           E – Block
  S / ↓        – CROUCH         Q while crouching – Sweep kick (low hit)
  ESC – Quit   F2 – webcam      F3 – on-screen buttons

Webcam (MediaPipe Pose):
  Right arm extended outward → PUNCH (one action per extension)
  Left hand held near head    → BLOCK (hold to defend)
  Lean torso left/right      → MOVE
  Both knees above hips      → JUMP
  Shoulders dropped low      → CROUCH 
"""
import sys, math, random, threading, time, collections
import pygame

try:
    import cv2, mediapipe as mp, numpy as np
    WEBCAM_AVAILABLE = True
except ImportError:
    WEBCAM_AVAILABLE = False

pygame.init()

IS_MOBILE = sys.platform in ("android", "ios")
if IS_MOBILE:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)

pygame.display.set_caption("SHADOW-BOXER  |  Shadow Fight 4 Edition")
clock = pygame.time.Clock()

# ──────────────────────────── palette ───────────────────────────────────────
C_BLACK  = (0,   0,   0  )
C_BG     = (5,   3,   12 )
C_SHADOW = (6,   4,   16 )   # near-invisible silhouette fill

P_GLOW   = (80,  180, 255)   # player (blue Herald)
P_GLOW2  = (140, 220, 255)
P_CORE   = (220, 245, 255)
B_GLOW   = (255, 70,  30 )   # bot (red Legion)
B_GLOW2  = (255, 150, 50 )
B_CORE   = (255, 230, 140)

GOLD     = (255, 200, 60 )
WHITE    = (240, 240, 255)
GREY     = (80,  80,  110)
GREEN    = (60,  230, 110)
RED_HIT  = (255, 30,  30 )
PURPLE   = (160, 60,  255)

# ──────────────────────────── fonts ─────────────────────────────────────────
def _font(size, bold=False):
    for n in ("Arial", "Helvetica Neue", "DejaVu Sans", "Liberation Sans"):
        try:
            f = pygame.font.SysFont(n, size, bold=bold)
            if f:
                return f
        except:
            pass
    return pygame.font.Font(None, size)


# Clean, readable typography
Fxs  = _font(14)
Fsm  = _font(18)
Fmd  = _font(26, bold=True)
Flg  = _font(44, bold=True)
Fxl  = _font(72, bold=True)
Fhud = _font(20, bold=True)
Fgesture = _font(24, bold=True)


def txt(surf, s, x, y, col=WHITE, f=Fmd, anchor="topleft", shd=True):
    img = f.render(s, True, col)
    r   = img.get_rect(**{anchor:(int(x),int(y))})
    if shd:
        sh = f.render(s, True, (0,0,0)); surf.blit(sh,(r.x+2,r.y+2))
    surf.blit(img, r)

# ──────────────────────────── glow / bloom ───────────────────────────────────
_gcache = {}
def glow_circ(surf, col, ctr, r, strength=150):
    k=(col,r)
    if k not in _gcache:
        s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        for rr in range(r,0,-max(1,r//24)):
            a=int(strength*(1-(rr/r))**0.55)
            if a>0: pygame.draw.circle(s,(*col,a),(r,r),rr)
        _gcache[k]=s
    surf.blit(_gcache[k],(ctr[0]-r,ctr[1]-r),special_flags=pygame.BLEND_RGBA_ADD)

def glow_line(surf, col, p1, p2, w, gr=16, s=100):
    gs=pygame.Surface(surf.get_size(),pygame.SRCALPHA)
    pygame.draw.line(gs,(*col,s//2),p1,p2,w+gr)
    surf.blit(gs,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
    if w>0: pygame.draw.line(surf,col,p1,p2,w)

# ──────────────────────────── screen shake ───────────────────────────────────
class Shake:
    def __init__(self): self.t=0; self.m=0
    def trigger(self,m=8,d=10): self.m=m; self.t=d
    def off(self):
        if self.t<=0: return (0,0)
        self.t-=1
        m=self.m*(self.t/10)
        return (random.randint(-int(m),int(m)), random.randint(-int(m),int(m)))

# ──────────────────────────── floating numbers ───────────────────────────────
class DmgNumber:
    __slots__=("x","y","val","life","col","crit")
    def __init__(self,x,y,val,col,crit=False):
        self.x=float(x); self.y=float(y); self.val=val
        self.life=55; self.col=col; self.crit=crit
    def update(self): self.y-=1.4; self.life-=1; return self.life>0
    def draw(self,surf):
        a=min(255,int(255*self.life/55))
        f=Flg if self.crit else Fmd
        s=f.render(("-"+str(self.val)) if not self.crit else f"💥{self.val}!",True,self.col)
        s.set_alpha(a); surf.blit(s,(int(self.x)-s.get_width()//2,int(self.y)))

# ──────────────────────────── particles ──────────────────────────────────────
class Particle:
    __slots__=("x","y","vx","vy","life","ml","col","sz","glow")
    def __init__(self,x,y,col,spd=6,glow=False):
        a=random.uniform(0,math.tau); v=random.uniform(spd*.3,spd)
        self.x=float(x);self.y=float(y);self.vx=math.cos(a)*v
        self.vy=math.sin(a)*v-random.uniform(0,3)
        self.ml=random.randint(22,48);self.life=self.ml
        self.col=col;self.sz=random.uniform(2,8);self.glow=glow
    def update(self): self.x+=self.vx;self.y+=self.vy;self.vy+=0.26;self.vx*=.96;self.life-=1;return self.life>0
    def draw(self,surf):
        f=self.life/self.ml; r,g,b=self.col
        c=(min(255,int(r*f+255*(1-f)*.3)),min(255,int(g*f)),min(255,int(b*f)))
        s=max(1,int(self.sz*f))
        if self.glow: glow_circ(surf,c,(int(self.x),int(self.y)),s*4,int(70*f))
        pygame.draw.circle(surf,c,(int(self.x),int(self.y)),s)

class Trail:
    def __init__(self,pts,col,w=3): self.pts=list(pts);self.col=col;self.ml=14;self.life=14;self.w=w
    def update(self): self.life-=1;return self.life>0
    def draw(self,surf):
        if len(self.pts)<2: return
        f=self.life/self.ml; r,g,b=self.col; c=(int(r*f),int(g*f),int(b*f))
        for i in range(len(self.pts)-1):
            glow_line(surf,c,self.pts[i],self.pts[i+1],max(1,int(self.w*f)),8,int(55*f))

class Ember:
    """Atmospheric slow-drifting ember particle."""
    __slots__=("x","y","vx","vy","life","ml","col","sz")
    def __init__(self,w,h,col):
        self.x=random.uniform(0,w); self.y=random.uniform(-20,h*0.6)
        self.vx=random.uniform(-0.4,0.4); self.vy=random.uniform(0.2,0.8)
        self.ml=random.randint(180,350); self.life=self.ml
        self.col=col; self.sz=random.uniform(1,3)
    def update(self): self.x+=self.vx+math.sin(self.life*.04)*.5;self.y+=self.vy;self.life-=1;return self.life>0
    def draw(self,surf):
        f=min(1,self.life/self.ml*2); a=int(180*f)
        s=pygame.Surface((int(self.sz*2+2),int(self.sz*2+2)),pygame.SRCALPHA)
        pygame.draw.circle(s,(*self.col,a),(int(self.sz+1),int(self.sz+1)),int(self.sz))
        surf.blit(s,(int(self.x),int(self.y)),special_flags=pygame.BLEND_RGBA_ADD)

_shockwaves=[]
def emit_sw(cx,cy,col,mr=100): _shockwaves.append([cx,cy,col,0,mr])
def draw_sw(surf):
    keep=[]
    for sw in _shockwaves:
        cx,cy,col,r,mr=sw; r+=8; sw[3]=r
        if r<mr:
            f=1-r/mr; a=int(220*f)
            s=pygame.Surface(surf.get_size(),pygame.SRCALPHA)
            pygame.draw.circle(s,(*col,a),(cx,cy),int(r),max(2,int(6*f)))
            surf.blit(s,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
            # second inner ring (double ring effect)
            if r>20:
                r2=int(r*0.6)
                pygame.draw.circle(s,(*col,int(a*0.5)),(cx,cy),r2,max(1,int(3*f)))
                surf.blit(s,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
            keep.append(sw)
    _shockwaves[:]=keep

class Particles:
    def __init__(self): self.p=[];self.trails=[];self.dmg=[];self.embers=[]
    def emit(self,x,y,col,n=14,spd=6,glow=True):
        for _ in range(n): self.p.append(Particle(x,y,col,spd,glow))
    def emit_spark(self,x,y,col,n=8):
        for _ in range(n):
            p=Particle(x,y,col,random.uniform(3,10),False)
            p.vy-=random.uniform(1,4); self.p.append(p)
    def add_trail(self,pts,col,w=3): self.trails.append(Trail(pts,col,w))
    def add_dmg(self,x,y,val,col,crit=False): self.dmg.append(DmgNumber(x,y,val,col,crit))
    def spawn_ember(self,w,h,col): self.embers.append(Ember(w,h,col))
    def update_draw(self,surf):
        self.p=[p for p in self.p if p.update()]; [p.draw(surf) for p in self.p]
        self.trails=[t for t in self.trails if t.update()]; [t.draw(surf) for t in self.trails]
        self.dmg=[d for d in self.dmg if d.update()]; [d.draw(surf) for d in self.dmg]
        self.embers=[e for e in self.embers if e.update()]; [e.draw(surf) for e in self.embers]

# ──────────────────────────── webcam pose ────────────────────────────────────
class PoseTracker:
    def __init__(self):
        self.running = False
        self.frame = None
        self.actions = set()
        self.status = "STARTING"
        self.calibrated = False

        self._lock = threading.Lock()
        self._thread = None
        self._calibration_requested = threading.Event()
        # Preserve pulse events until the Pygame loop reads them.
        self._pending_punch = False
        self._pending_punch_since = 0.0
        self._last_punch_seen = 0.0
        self._punch_count = 0

    def start(self):
        if not WEBCAM_AVAILABLE:
            self.status = "WEBCAM LIBRARIES NOT AVAILABLE"
            return False

        self.running = True
        self._thread = threading.Thread(
            target=self._run,
            daemon=True
        )
        self._thread.start()
        return True

    def stop(self):
        self.running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def request_calibration(self):
        self._calibration_requested.set()

    def get_actions(self, accept_punch=True):
        with self._lock:
            actions = set(self.actions)
            # A punch is an event, not a held pose. Buffer briefly if the
            # fighter is momentarily stunned or already mid-punch.
            actions.discard("PUNCH")
            if self._pending_punch and (time.monotonic() - self._pending_punch_since) > 0.85:
                self._pending_punch = False
            if self._pending_punch and accept_punch:
                actions.add("PUNCH")
                self._pending_punch = False
            return actions

    def get_frame(self):
        with self._lock:
            return self.frame.copy() if self.frame is not None else None

    def get_status(self):
        with self._lock:
            if time.monotonic() - self._last_punch_seen < 0.65:
                return f"PUNCH DETECTED #{self._punch_count}", self.calibrated
            return self.status, self.calibrated

    def _run(self):
        detector = None

        try:
            from gesture_detector import GestureDetector

            detector = GestureDetector(show_preview=False)

            with self._lock:
                self.status = detector.status

            while self.running:
                actions = detector.update_actions()

                if self._calibration_requested.is_set():
                    self._calibration_requested.clear()
                    detector.calibrate()

                frame = detector.last_frame
                calibrated = detector.is_calibrated

                with self._lock:
                    self.actions = actions
                    if "PUNCH" in actions:
                        self._pending_punch = True
                        self._pending_punch_since = time.monotonic()
                        self._last_punch_seen = self._pending_punch_since
                        self._punch_count += 1
                    self.frame = frame.copy() if frame is not None else None
                    self.status = detector.status
                    self.calibrated = calibrated

        except Exception as error:
            with self._lock:
                self.status = f"WEBCAM ERROR: {error}"
                self.actions = set()
                self._pending_punch = False

        finally:
            if detector is not None:
                detector.close()

            with self._lock:
                self.actions = set()
                self._pending_punch = False
                self.frame = None
# ═══════════════════════════════════════════════════════════════════════════
class Fighter:
    IDLE="idle";WALK="walk";JUMP="jump";DUCK="duck"
    PUNCH="punch";SWEEP="sweep";BLOCK="block";HIT="hit";KO="ko"

    def __init__(self,x,facing,gc,gc2,gcore,name,is_player=True):
        self.name=name;self.facing=facing;self.is_player=is_player
        self.glow=gc;self.glow2=gc2;self.core=gcore
        self.x=float(x);self.y=0.0;self.vy=0.0
        self.health=100;self.max_health=100
        self.state=Fighter.IDLE;self.state_time=0
        self.punch_timer=0;self.hit_timer=0;self.block_timer=0
        self.combo=0;self.shadow_energy=0.0;self.aura_pulse=0.0
        self._fist_hist=collections.deque(maxlen=8)
        # landing dust
        self._was_air=False

    def ground_px(self,L): return L["ground"]+int(self.y)
    def center_x(self,L):  return int(self.x+L["fw"]/2)

    # ── hitbox height bands (relative to ground, as negative = upward) ────────
    def hbox_top(self,L):
        """Top of hitbox in pixels above ground (negative number)."""
        fh=L["fh"]
        if self.state==Fighter.DUCK: return int(-fh*0.42)   # crouch = only lower half
        return int(-fh*0.88)                                  # standing = full height

    def hbox_bot(self,L):
        fh=L["fh"]
        if self.state==Fighter.DUCK: return int(-fh*0.04)
        return int(-fh*0.10)

    # Height of outgoing punch (attacker reference, negative = above ground)
    def punch_height(self,L):
        fh=L["fh"]
        if self.state in (Fighter.SWEEP,):   return int(-fh*0.18)   # low sweep
        if self.state==Fighter.JUMP:          return int(-fh*0.65)+int(self.y)
        return int(-fh*0.60)                                          # standing punch

    def fist_pos(self,L):
        fw=L["fw"];fh=L["fh"];gy=self.ground_px(L)
        body_top=gy-int(fh*0.78)
        arm_root_y=body_top+int(fh*0.18)
        if self.state==Fighter.PUNCH:
            return (int(self.center_x(L)+self.facing*int(fw*0.95)),arm_root_y+int(fh*0.08))
        if self.state==Fighter.SWEEP:
            return (int(self.center_x(L)+self.facing*int(fw*1.10)),gy-int(fh*0.18))
        return (int(self.center_x(L)+self.facing*int(fw*0.55)),arm_root_y+int(fh*0.22))

    # ── update ────────────────────────────────────────────────────────────────
    def update(self,L,actions,opp,parts,shake,dt):
        if self.state==Fighter.KO: return
        fw=L["fw"];W=L["width"]
        self.state_time+=1
        if self.punch_timer>0: self.punch_timer-=1
        if self.hit_timer>0:   self.hit_timer-=1
        if self.block_timer>0: self.block_timer-=1
        self.aura_pulse=(self.aura_pulse+0.07)%math.tau
        self.shadow_energy=min(100,self.shadow_energy+0.04)

        was_air=self.y<0
        spd=L["speed"]*dt

        # ── PRIORITY ORDER ───────────────────────────────────────────────
        # 1. HIT stun: can't act during stun
        if self.state==Fighter.HIT:
            if self.hit_timer==0: self.set_state(Fighter.IDLE)
            # still apply gravity
            self._apply_gravity(L,dt)
            return

        # 2. CROUCH (highest movement priority while on ground)
        ducking="DUCK" in actions and self.y==0
        if ducking:
            if self.state!=Fighter.DUCK: self.set_state(Fighter.DUCK)
            # Crouch-punch = SWEEP KICK
            if "PUNCH" in actions and self.punch_timer==0:
                self.set_state(Fighter.SWEEP)
                self.punch_timer=24
                self._try_hit(opp,L,parts,shake,is_sweep=True)
            # block while crouching
            if "BLOCK" in actions: self.block_timer=10
            self._apply_gravity(L,dt)
            self._face_opp(opp)
            self._fist_trail(parts,L)
            return

        # 3. Release crouch → idle
        if self.state==Fighter.DUCK and not ducking:
            self.set_state(Fighter.IDLE)

        # 4. JUMP
        if "JUMP" in actions and self.y==0 and self.vy==0:
            self.vy=L["jump_v"]
            self.set_state(Fighter.JUMP)

        # 5. PUNCH (standing or in-air)
        if "PUNCH" in actions and self.punch_timer==0 and self.state not in (Fighter.HIT,Fighter.KO):
            self.set_state(Fighter.PUNCH)
            self.punch_timer=22
            self._try_hit(opp,L,parts,shake,is_sweep=False)

        # 6. BLOCK
        if "BLOCK" in actions:
            self.block_timer=10
            if self.state not in (Fighter.PUNCH,Fighter.JUMP,Fighter.SWEEP):
                self.set_state(Fighter.BLOCK)

        # 7. MOVE
        moving=False
        if "LEFT" in actions and self.state not in (Fighter.PUNCH,Fighter.SWEEP):
            self.x-=spd; self.facing=-1; moving=True
            if self.state not in (Fighter.JUMP,): self.set_state(Fighter.WALK)
        if "RIGHT" in actions and self.state not in (Fighter.PUNCH,Fighter.SWEEP):
            self.x+=spd; self.facing=+1; moving=True
            if self.state not in (Fighter.JUMP,): self.set_state(Fighter.WALK)
        self.x=max(0,min(self.x,W-fw))

        # 8. State resets
        if self.state==Fighter.PUNCH and self.punch_timer==0: self.set_state(Fighter.IDLE)
        if self.state==Fighter.SWEEP  and self.punch_timer==0: self.set_state(Fighter.IDLE)
        if self.state==Fighter.BLOCK  and self.block_timer==0 and "BLOCK" not in actions: self.set_state(Fighter.IDLE)
        if self.state==Fighter.WALK   and not moving: self.set_state(Fighter.IDLE)
        if self.state==Fighter.JUMP   and self.y==0: self.set_state(Fighter.IDLE)

        self._apply_gravity(L,dt)
        self._face_opp(opp)
        self._fist_trail(parts,L)

        # Landing dust
        if was_air and self.y==0:
            cx=self.center_x(L); gy=self.ground_px(L)
            parts.emit(cx,gy,self.glow,12,3,False)
            parts.emit_spark(cx,gy,self.glow2,6)

    def _apply_gravity(self,L,dt):
        if self.y<0 or self.vy<0:
            self.vy+=L["gravity"]*dt; self.y+=self.vy*dt
            if self.y>=0: self.y=0; self.vy=0

    def _face_opp(self,opp):
        if opp and self.state in (Fighter.IDLE,Fighter.WALK,Fighter.DUCK):
            self.facing=+1 if opp.x>self.x else -1

    def _fist_trail(self,parts,L):
        fp=self.fist_pos(L); self._fist_hist.append(fp)
        if self.state in (Fighter.PUNCH,Fighter.SWEEP) and self.state_time<14:
            pts=list(self._fist_hist)
            if len(pts)>=2: parts.add_trail(pts,self.glow,4)

    def set_state(self,s):
        if self.state!=s: self.state=s; self.state_time=0

    def receive_hit(self,dmg,parts,L,shake,low=False):
        blocked=self.state==Fighter.BLOCK and not low  # block only stops high hits
        if blocked: dmg=max(1,dmg//5)
        crit=(dmg>=18)
        self.health=max(0,self.health-dmg)
        if not blocked:
            self.set_state(Fighter.HIT); self.hit_timer=15
        cx=self.center_x(L)
        # hit y = head/torso or legs
        hy=self.ground_px(L)+(self.hbox_top(L)+self.hbox_bot(L))//2
        col=self.glow
        parts.emit(int(cx),int(hy),col,20,8,True)
        parts.emit_spark(int(cx),int(hy),self.core,10)
        parts.add_dmg(int(cx),int(hy-20),dmg,col,crit)
        if not blocked:
            shake.trigger(10 if crit else 6, 12)
            emit_sw(int(cx),int(hy),col,110 if crit else 75)
        if self.health==0: self.set_state(Fighter.KO)

    def _try_hit(self,opp,L,parts,shake,is_sweep):
        if opp is None or opp.state==Fighter.KO: return
        dist=abs(self.center_x(L)-opp.center_x(L))
        reach=L["fw"]*(1.8 if is_sweep else 1.6)
        if dist>=reach: self.combo=0; return

        # Height check: punch height must land within opponent hitbox band
        ph=self.punch_height(L)
        opp_ground=opp.ground_px(L)
        opp_top=opp_ground+opp.hbox_top(L)
        opp_bot=opp_ground+opp.hbox_bot(L)
        punch_y=opp_ground+ph

        if not (opp_top <= punch_y <= opp_bot):
            # swing and miss – still play miss spark
            mx,my=self.fist_pos(L)
            parts.emit_spark(mx,my,GREY,4)
            # small "MISS" text
            parts.add_dmg(mx,my-10,0,GREY,False)
            self.combo=0; return

        dmg=random.randint(5,13) if is_sweep else random.randint(8,20)
        if self.shadow_energy>=50:
            dmg=int(dmg*1.6); self.shadow_energy=0
        opp.receive_hit(dmg,parts,L,shake,low=is_sweep)
        self.combo+=1
        self.shadow_energy=min(100,self.shadow_energy+9)

    # ── DRAW ─────────────────────────────────────────────────────────────────
    def draw(self,surf,L):
        t=pygame.time.get_ticks()
        fw=L["fw"];fh=L["fh"];gy=self.ground_px(L);cx=self.center_x(L);f=self.facing
        col=C_SHADOW

        duck =self.state==Fighter.DUCK
        punch=self.state==Fighter.PUNCH
        sweep=self.state==Fighter.SWEEP
        block=self.state==Fighter.BLOCK
        hit  =self.state==Fighter.HIT
        ko   =self.state==Fighter.KO
        walk =self.state==Fighter.WALK
        jump =self.state==Fighter.JUMP
        idle =self.state==Fighter.IDLE
        bob  =math.sin(t/160)*fh*.010 if idle else 0

        # ── measurements ──────────────────────────────────────────────────
        if duck or sweep:
            body_top=gy-int(fh*.38); body_h=int(fh*.30)
            head_cy =gy-int(fh*.41); head_r=max(8,int(fh*.125))
            leg_root=gy-int(fh*.16)
            shin_end_l=(cx-int(fw*.45),gy); shin_end_r=(cx+int(fw*.45),gy)
        elif ko:
            body_top=gy-int(fh*.16); body_h=int(fh*.12)
            head_cy =gy-int(fh*.18); head_r=max(8,int(fh*.12))
            leg_root=gy-int(fh*.07)
            shin_end_l=shin_end_r=(cx,gy)
        else:
            body_top=int(gy-fh*.76+bob); body_h=int(fh*.46)
            head_cy =int(gy-fh*.88+bob); head_r=max(10,int(fh*.135))
            leg_root=gy-int(fh*.26)
            walk_sw =math.sin(t/90)*fw*.28 if walk else (math.sin(t/120)*fw*.14 if jump else 0)
            shin_end_l=(int(cx-fw*.24+walk_sw),gy)
            shin_end_r=(int(cx+fw*.24-walk_sw),gy)

        body_x=int(cx-fw*.33); body_w=int(fw*.66)
        arm_root_y=body_top+int(fh*.17)
        glove_r=max(7,int(fh*.10))
        leg_w=max(5,fw//7)

        # ── 1. AMBIENT AURA ───────────────────────────────────────────────
        pulse=.5+.5*math.sin(self.aura_pulse)
        ar=int(fh*.60+pulse*fh*.07); aa=int(25+pulse*15)
        au=pygame.Surface((ar*2,ar*2),pygame.SRCALPHA)
        for rr in range(ar,0,-max(1,ar//8)):
            a2=int(aa*(1-rr/ar))
            if a2>0: pygame.draw.circle(au,(*self.glow,a2),(ar,ar),rr)
        surf.blit(au,(cx-ar,gy-fh//2-ar//2),special_flags=pygame.BLEND_RGBA_ADD)

        # ── 2. FLOOR DYNAMIC LIGHT ────────────────────────────────────────
        fl=pygame.Surface((fw*4,int(fh*.15)),pygame.SRCALPHA)
        pygame.draw.ellipse(fl,(*self.glow,int(35+15*pulse)),fl.get_rect())
        surf.blit(fl,(cx-fw*2,gy-int(fh*.04)),special_flags=pygame.BLEND_RGBA_ADD)

        # ── 3. GROUND SHADOW ──────────────────────────────────────────────
        sh_w=int(fw*1.4); sh_h=int(fh*.05)
        sh=pygame.Surface((sh_w,sh_h),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,110),sh.get_rect())
        surf.blit(sh,(cx-sh_w//2,gy-sh_h//2))

        # ── 4. FLOOR REFLECTION ──────────────────────────────────────────
        # Only draw reflection if not KO, as a flipped ghost below the floor line
        if not ko:
            self._draw_reflection(surf,L,cx,gy,fw,fh,head_r,body_x,body_w,
                                   body_top,body_h,leg_root,arm_root_y,
                                   duck,sweep,f,bob)

        # ── 5. KO POSE ────────────────────────────────────────────────────
        if ko:
            pygame.draw.rect(surf,col,(int(cx-fw*1.1),gy-int(fh*.16),int(fw*2.2),int(fh*.16)),border_radius=10)
            pygame.draw.circle(surf,col,(int(cx+f*fw*.7),gy-int(fh*.13)),head_r)
            glow_circ(surf,self.glow,(cx,gy-int(fh*.08)),int(fh*.5),25)
            return

        # ── 6. LEGS ───────────────────────────────────────────────────────
        # Thigh joint
        thigh_top=(cx,leg_root)
        if duck or sweep:
            # Both thighs bent outward, shins down
            thigh_knee_l=(cx-int(fw*.30), gy-int(fh*.12))
            thigh_knee_r=(cx+int(fw*.30), gy-int(fh*.12))
            pygame.draw.line(surf,col,thigh_top,thigh_knee_l,leg_w)
            pygame.draw.line(surf,col,thigh_top,thigh_knee_r,leg_w)
            glow_line(surf,self.glow,thigh_top,thigh_knee_l,1,3,12)
            glow_line(surf,self.glow,thigh_top,thigh_knee_r,1,3,12)
            # Shins
            pygame.draw.line(surf,col,thigh_knee_l,shin_end_l,leg_w)
            pygame.draw.line(surf,col,thigh_knee_r,shin_end_r,leg_w)
            glow_line(surf,self.glow,thigh_knee_l,shin_end_l,1,3,10)
            glow_line(surf,self.glow,thigh_knee_r,shin_end_r,1,3,10)
            # Knee caps
            pygame.draw.circle(surf,col,thigh_knee_l,int(leg_w*.8))
            pygame.draw.circle(surf,col,thigh_knee_r,int(leg_w*.8))
            glow_circ(surf,self.glow,thigh_knee_l,int(leg_w*1.4),30)
            glow_circ(surf,self.glow,thigh_knee_r,int(leg_w*1.4),30)
            # Feet / boots
            pygame.draw.ellipse(surf,col,(shin_end_l[0]-int(fw*.14),gy-int(fh*.05),
                                           int(fw*.28),int(fh*.06)))
            pygame.draw.ellipse(surf,col,(shin_end_r[0]-int(fw*.14),gy-int(fh*.05),
                                           int(fw*.28),int(fh*.06)))
        else:
            # Standing / walking – two separate legs with knee joints
            knee_l=(int(cx-fw*.14+walk_sw*.4),gy-int(fh*.13))
            knee_r=(int(cx+fw*.14-walk_sw*.4),gy-int(fh*.13))
            # Thighs
            pygame.draw.line(surf,col,thigh_top,knee_l,leg_w)
            pygame.draw.line(surf,col,thigh_top,knee_r,leg_w)
            glow_line(surf,self.glow,thigh_top,knee_l,1,3,12)
            glow_line(surf,self.glow,thigh_top,knee_r,1,3,12)
            # Shins
            pygame.draw.line(surf,col,knee_l,shin_end_l,leg_w)
            pygame.draw.line(surf,col,knee_r,shin_end_r,leg_w)
            glow_line(surf,self.glow,knee_l,shin_end_l,1,3,10)
            glow_line(surf,self.glow,knee_r,shin_end_r,1,3,10)
            # Knee caps
            for kp in (knee_l,knee_r):
                pygame.draw.circle(surf,col,kp,int(leg_w*.8))
                glow_circ(surf,self.glow,kp,int(leg_w*1.5),25)
            # Boot / feet
            for se in (shin_end_l,shin_end_r):
                pygame.draw.ellipse(surf,col,(se[0]-int(fw*.14),gy-int(fh*.05),
                                               int(fw*.28),int(fh*.06)))
                glow_circ(surf,self.glow,(se[0],gy),int(fw*.12),15)

        # ── 7. BELT (waist detail) ─────────────────────────────────────────
        belt_y=body_top+body_h-int(fh*.05)
        pygame.draw.rect(surf,col,(body_x,belt_y,body_w,int(fh*.04)),border_radius=3)
        glow_line(surf,self.glow2,(body_x,belt_y+int(fh*.02)),(body_x+body_w,belt_y+int(fh*.02)),1,4,20)

        # ── 8. TORSO ──────────────────────────────────────────────────────
        tilt=int(fw*.07*(-f)) if hit else 0
        pygame.draw.rect(surf,col,(body_x+tilt,body_top,body_w,body_h),border_radius=10)
        # Pectoral / shoulder detail lines (subtle)
        for lf in (-.20,+.20):
            lx=int(cx+fw*lf)+tilt
            pygame.draw.line(surf,C_SHADOW,(lx,body_top+int(fh*.04)),(lx,body_top+int(fh*.28)),max(1,int(fw*.04)))
        # Collar bone hints
        pygame.draw.line(surf,col,
                        (body_x+tilt+int(fw*.15),body_top+int(fh*.04)),
                        (body_x+tilt+int(fw*.50),body_top+int(fh*.04)),max(2,int(fw*.03)))
        # Body rim glow
        rims=pygame.Surface((body_w+8,body_h+8),pygame.SRCALPHA)
        pygame.draw.rect(rims,(*self.glow,30),(0,0,body_w+8,body_h+8),border_radius=11)
        surf.blit(rims,(body_x+tilt-4,body_top-4),special_flags=pygame.BLEND_RGBA_ADD)

        # ── 9. HEAD ───────────────────────────────────────────────────────
        # skull
        pygame.draw.circle(surf,col,(cx,head_cy),head_r)
        # jaw / chin bump
        pygame.draw.ellipse(surf,col,(cx-int(head_r*.55),head_cy,int(head_r*1.1),int(head_r*.75)))
        # Helmet ridge
        pts_helm=[(cx-head_r,head_cy-int(head_r*.3)),
                   (cx,       head_cy-int(head_r*.95)),
                   (cx+head_r,head_cy-int(head_r*.3))]
        pygame.draw.polygon(surf,col,pts_helm)
        glow_line(surf,self.glow2,(cx-head_r+2,head_cy-int(head_r*.28)),
                                   (cx+head_r-2,head_cy-int(head_r*.28)),1,4,18)
        # Visor slit (glowing eye band)
        vis_y=head_cy-int(head_r*.10)
        vis_h=int(head_r*.28)
        pygame.draw.rect(surf,(*self.core,220),(cx-int(head_r*.7),vis_y,int(head_r*1.4),vis_h),border_radius=3)
        glow_circ(surf,self.core,(cx,vis_y+vis_h//2),int(head_r*.9),180)
        # ear
        pygame.draw.ellipse(surf,col,(cx-head_r-int(head_r*.3),head_cy-int(head_r*.2),
                                       int(head_r*.35),int(head_r*.45)))

        # ── 10. SHADOW ENERGY mini-bar (below feet) ───────────────────────
        se_w=int(fw*.9); se_h=4; se_x=cx-se_w//2; se_y=gy+10
        pygame.draw.rect(surf,(18,16,38),(se_x,se_y,se_w,se_h),border_radius=2)
        fill=int(se_w*self.shadow_energy/100)
        if fill>0:
            pygame.draw.rect(surf,self.glow,(se_x,se_y,fill,se_h),border_radius=2)
            gs=pygame.Surface((fill,se_h),pygame.SRCALPHA)
            pygame.draw.rect(gs,(*self.glow,70),(0,0,fill,se_h),border_radius=2)
            surf.blit(gs,(se_x,se_y),special_flags=pygame.BLEND_RGBA_ADD)

        # ── 11. BACK ARM ──────────────────────────────────────────────────
        bax=cx-f*int(fw*.32); bgy_up=arm_root_y; bgx=cx-f*int(fw*.10); bgly=arm_root_y+int(fh*.26)
        pygame.draw.line(surf,col,(bax,bgy_up),(bgx,bgly),max(4,fw//8))
        glow_line(surf,self.glow,(bax,bgy_up),(bgx,bgly),1,4,15)
        # elbow joint
        pygame.draw.circle(surf,col,(bgx,bgly),max(4,fw//10))
        glow_circ(surf,self.glow,(bgx,bgly),max(5,fw//8),25)
        pygame.draw.circle(surf,col,(bgx,bgly),glove_r-3)
        glow_circ(surf,self.glow,(bgx,bgly),glove_r+5,35)

        # ── 12. FRONT ARM ─────────────────────────────────────────────────
        fax=cx+f*int(fw*.30)
        if punch:
            fgx=cx+f*int(fw*.95); fgy=arm_root_y+int(fh*.08); pg=1-self.punch_timer/22
            # elbow midpoint
            mid_x=int((fax+fgx)*.55); mid_y=arm_root_y+int(fh*.05)
        elif sweep:
            fgx=cx+f*int(fw*1.10); fgy=gy-int(fh*.18); pg=1-self.punch_timer/24
            mid_x=int((fax+fgx)*.5); mid_y=arm_root_y+int(fh*.35)
        elif block:
            fgx=cx+f*int(fw*.18); fgy=arm_root_y-int(fh*.10); pg=0
            mid_x=int((fax+fgx)*.5); mid_y=arm_root_y+int(fh*.02)
        else:
            fgx=cx+f*int(fw*.60); fgy=arm_root_y+int(fh*.22); pg=0
            mid_x=int((fax+fgx)*.5); mid_y=arm_root_y+int(fh*.20)

        # 2-segment arm: upper + lower
        pygame.draw.line(surf,col,(fax,arm_root_y),(mid_x,mid_y),max(4,fw//8))
        glow_line(surf,self.glow,(fax,arm_root_y),(mid_x,mid_y),1,4,18)
        pygame.draw.line(surf,col,(mid_x,mid_y),(fgx,fgy),max(3,fw//9))
        glow_line(surf,self.glow,(mid_x,mid_y),(fgx,fgy),1,4,16)
        # elbow joint
        pygame.draw.circle(surf,col,(mid_x,mid_y),max(4,fw//10))
        glow_circ(surf,self.glow,(mid_x,mid_y),max(5,fw//8),30)

        # Glove
        pygame.draw.circle(surf,col,(fgx,fgy),glove_r)
        g_str=int(200*pg)+55 if (punch or sweep) else 55
        glow_circ(surf,self.glow,(fgx,fgy),glove_r+8,g_str)
        if (punch or sweep) and pg>.45:
            glow_circ(surf,self.core,(fgx,fgy),glove_r+5,int(255*pg))

        # ── 13. SWEEP KICK FOOT ───────────────────────────────────────────
        if sweep:
            # draw extending leg kick
            kp=(cx+f*int(fw*.55),gy-int(fh*.16))
            pygame.draw.line(surf,col,(cx,gy-int(fh*.20)),(fgx,fgy),leg_w+2)
            glow_line(surf,self.glow,(cx,gy-int(fh*.20)),(fgx,fgy),2,6,80)
            pygame.draw.ellipse(surf,col,(fgx-int(fw*.18),fgy-int(fh*.04),int(fw*.36),int(fh*.07)))

        # ── 14. BLOCK SHIELD ──────────────────────────────────────────────
        if block:
            sh=pygame.Surface((fw*2,int(fh*.8)),pygame.SRCALPHA)
            for rr in range(int(fw*.9),0,-6):
                a3=int(45*(1-rr/(fw*.9)))
                pygame.draw.circle(sh,(*self.glow,a3),(int(fw*.5+f*fw*.4),int(fh*.4)),rr)
            surf.blit(sh,(cx-int(fw*.5),arm_root_y-int(fh*.2)),special_flags=pygame.BLEND_RGBA_ADD)

        # ── 15. HIT TINT ──────────────────────────────────────────────────
        if hit and self.hit_timer>8:
            tint=pygame.Surface((fw*2,fh+30),pygame.SRCALPHA)
            tint.fill((*RED_HIT,50)); surf.blit(tint,(cx-fw,body_top-15))

        # ── 16. WALK SPARKS ───────────────────────────────────────────────
        if walk and random.random()<.25:
            sx=cx+random.randint(-int(fw*.3),int(fw*.3)); sy=gy-random.randint(0,6)
            gs=pygame.Surface((10,10),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*self.glow,110),(5,5),3)
            surf.blit(gs,(sx-5,sy-5),special_flags=pygame.BLEND_RGBA_ADD)

        # ── 17. CROUCH AURA PULSE ─────────────────────────────────────────
        if duck or sweep:
            cr=int(fw*.8+pulse*fw*.12)
            cs=pygame.Surface((cr*2,cr),pygame.SRCALPHA)
            pygame.draw.ellipse(cs,(*self.glow,int(30+pulse*20)),(0,0,cr*2,cr))
            surf.blit(cs,(cx-cr,gy-cr//2),special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_reflection(self,surf,L,cx,gy,fw,fh,head_r,body_x,body_w,
                          body_top,body_h,leg_root,arm_root_y,
                          duck,sweep,f,bob):
        """Mirror silhouette below the floor line with gradient fade."""
        # Only a simplified shape reflection for performance
        depth=int(fh*.40)  # how far below floor the reflection extends
        alpha_max=55
        for step,ratio in enumerate([.9,.65,.4,.2,.05]):
            dy=int(depth*step/4)
            a=int(alpha_max*ratio)
            if a<=0: continue
            # head
            hcy_r=gy+int((gy-body_top+head_r)*step*.16)+dy
            hcy_r=min(hcy_r,gy+dy+int(fh*.38))
            sr=max(2,int(head_r*(1-step*.12)))
            sh=pygame.Surface((sr*2,sr*2),pygame.SRCALPHA)
            pygame.draw.circle(sh,(*self.glow,a),(sr,sr),sr)
            surf.blit(sh,(cx-sr,gy+dy),special_flags=pygame.BLEND_RGBA_ADD)
            # body
            rh=max(4,int(body_h*(1-step*.15)))
            rs=pygame.Surface((body_w,rh),pygame.SRCALPHA)
            pygame.draw.rect(rs,(*self.glow,a//2),(0,0,body_w,rh),border_radius=8)
            surf.blit(rs,(body_x,gy+dy+int(head_r*.3)),special_flags=pygame.BLEND_RGBA_ADD)
        # gradient bar to erase reflection below certain depth
        fade=pygame.Surface((fw*4,depth+10),pygame.SRCALPHA)
        for dy in range(depth+10):
            fa=int(255*(dy/(depth+10))**1.5)
            pygame.draw.line(fade,(0,0,0,fa),(0,dy),(fw*4,dy))
        surf.blit(fade,(cx-fw*2,gy))


# ═══════════════════════════════════════════════════════════════════════════
#  BOT AI
# ═══════════════════════════════════════════════════════════════════════════
class BotAI:
    def __init__(self,f): self.f=f;self.state="approach";self.timer=0;self.react=0;self._last=set()
    def acts(self,player,L,t):
        a=set()
        if self.f.state==Fighter.KO: return a
        self.timer+=1; self.react+=1
        fw=L["fw"]; dist=abs(self.f.center_x(L)-player.center_x(L))
        close=fw*1.5; hp=self.f.health/100
        if self.react<9:
            for x in ("LEFT","RIGHT"):
                if x in self._last: a.add(x)
            return a
        self.react=0
        # state machine
        if hp<.22: self.state="evade"
        elif dist<close:
            if player.state==Fighter.PUNCH and random.random()<.42: self.state="defend"
            elif player.state==Fighter.DUCK and random.random()<.3:  self.state="sweep"
            else: self.state="attack"
        else: self.state="approach"
        # execute
        if self.state=="approach":
            a.add("RIGHT" if self.f.x<player.x else "LEFT")
        elif self.state=="attack":
            if dist>close*.55: a.add("RIGHT" if self.f.x<player.x else "LEFT")
            if self.timer%random.randint(12,22)==0: a.add("PUNCH")
            if self.timer%68==0: a.add("JUMP")
        elif self.state=="sweep":
            a.add("DUCK"); a.add("PUNCH")   # crouching punch = sweep
        elif self.state=="evade":
            a.add("LEFT" if self.f.x<player.x else "RIGHT")
            if random.random()<.05: a.add("JUMP")
        elif self.state=="defend":
            a.add("BLOCK")
            if self.timer%28==0: a.add("PUNCH")
        self._last=a; return a


# ═══════════════════════════════════════════════════════════════════════════
#  BACKGROUND  –  multi-layer dark fantasy (cached)
# ═══════════════════════════════════════════════════════════════════════════
_bg_cache={}
def _build_bg(w,h):
    s=pygame.Surface((w,h))
    # Sky gradient
    for y in range(h):
        f=y/h; r=int(4+f*8); g=int(2+f*4); b=int(10+f*22)
        pygame.draw.line(s,(r,g,b),(0,y),(w,y))
    # City silhouette
    random.seed(99)
    pts=[(0,int(h*.73))]
    x=0
    while x<w:
        bw=random.randint(50,170); bh=random.randint(int(h*.20),int(h*.48))
        # windowed building
        bx=x; btop=int(h*.73)-bh
        pts.append((bx,int(h*.73)-bh)); pts.append((bx+bw,int(h*.73)-bh))
        x+=bw
    pts+=([(w,int(h*.73)),(w,h),(0,h)])
    pygame.draw.polygon(s,(7,5,16),pts)
    # Windows in buildings (glow dots)
    random.seed(42)
    for _ in range(140):
        wx=random.randint(0,w); wy=random.randint(int(h*.28),int(h*.72))
        wc=random.choice([(180,160,80),(80,160,255),(200,80,80),(100,220,180)])
        pygame.draw.rect(s,wc,(wx,wy,random.randint(2,5),random.randint(2,4)))
    # Moon
    mc=(int(w*.78),int(h*.14)); mr=int(h*.075)
    pygame.draw.circle(s,(185,175,215),mc,mr)
    pygame.draw.circle(s,(155,145,190),mc,int(mr*.82))
    # Moon craters
    random.seed(7)
    for _ in range(5):
        crx=mc[0]+random.randint(-mr//2,mr//2); cry=mc[1]+random.randint(-mr//2,mr//2)
        pygame.draw.circle(s,(140,130,175),(crx,cry),random.randint(3,8))
    # Moon glow
    for rr in range(mr*4,mr,-5):
        a=int(18*(1-(rr-mr)/(mr*3)))
        if a>0:
            gs=pygame.Surface((rr*2,rr*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(160,150,220,a),(rr,rr),rr)
            s.blit(gs,(mc[0]-rr,mc[1]-rr),special_flags=pygame.BLEND_RGBA_ADD)
    # Aurora beams
    for i in range(3):
        ax=int(w*(.15+i*.32)); aw=int(w*.08)
        for ay in range(0,int(h*.65),3):
            aa=int(15*(1-ay/(h*.65)))
            ac=(30+i*20,aa,80+i*30,aa)
            gs=pygame.Surface((aw,3),pygame.SRCALPHA)
            gs.fill(ac); s.blit(gs,(ax-aw//2+int(math.sin(ay*.03)*aw*.5),ay),
                                special_flags=pygame.BLEND_RGBA_ADD)
    # Stars
    random.seed(42)
    for _ in range(240):
        sx=random.randint(0,w); sy=random.randint(0,int(h*.65))
        sb=random.randint(70,230)
        pygame.draw.circle(s,(sb,sb,min(255,sb+30)),(sx,sy),random.choice([1,1,1,2]))
    random.seed()
    return s

def draw_bg(surf,w,h,t,ox=0,oy=0):
    k=(w,h)
    if k not in _bg_cache: _bg_cache[k]=_build_bg(w,h)
    surf.blit(_bg_cache[k],(ox,oy))
    # Animated fog
    for i in range(6):
        fx=int((w*i/6+t*.014*(1-i%2*2))%w)
        fy=int(h*.60+math.sin(t*.001+i)*h*.04)
        fs=int(w*.20)
        fg=pygame.Surface((fs,int(h*.07)),pygame.SRCALPHA)
        pygame.draw.ellipse(fg,(38,28,65,18),fg.get_rect())
        surf.blit(fg,(fx-fs//2,fy),special_flags=pygame.BLEND_RGBA_ADD)
    # Crowd
    cy=int(h*.62)
    for i in range(65):
        bx=int(w*i/65); by=cy+int(math.sin(i*2.3+t*.0012)*h*.015)
        br=max(2,int(h*.011))
        sh=32+int(14*math.sin(i*.7+t*.012))
        pygame.draw.circle(surf,(sh,sh//2+8,sh+18),(bx,by),br)
        aa=math.sin(t*.003+i*.8)*.7
        pygame.draw.line(surf,(sh,sh//2,sh+12),(bx,by-br),(int(bx+br*1.5*math.sin(aa)),by-br*2-3),2)

def draw_arena(surf,w,h,ground):
    rt=int(h*.44); rb=ground+int(h*.025)
    # Canvas
    pygame.draw.rect(surf,(16,12,32),(int(w*.03),rt,int(w*.94),rb-rt))
    # Canvas grid lines
    for i in range(1,6):
        lx=int(w*(.03+i*.158))
        pygame.draw.line(surf,(24,19,45),(lx,rt),(lx,rb),1)
    for i in range(1,4):
        ly=int(rt+(rb-rt)*i/4)
        pygame.draw.line(surf,(24,19,45),(int(w*.03),ly),(int(w*.97),ly),1)
    # Ring ropes
    for ratio,dark,bright in [(.50,(130,18,18),(255,55,55)),
                                (.58,(90,90,105),(210,210,230)),
                                (.67,(130,18,18),(255,55,55))]:
        ry=int(h*ratio)
        pygame.draw.line(surf,dark,(int(w*.03),ry),(int(w*.97),ry),max(3,int(h*.006)))
        rs=pygame.Surface((w,10),pygame.SRCALPHA)
        pygame.draw.line(rs,(*bright,55),(int(w*.03),5),(int(w*.97),5),max(2,int(h*.004)))
        surf.blit(rs,(0,ry-5),special_flags=pygame.BLEND_RGBA_ADD)
    # Corner posts
    for px in (int(w*.03),int(w*.97)):
        pygame.draw.rect(surf,(110,110,130),(px-int(w*.009),rt,max(6,int(w*.018)),rb-rt))
        gs=pygame.Surface((32,rb-rt),pygame.SRCALPHA)
        pygame.draw.rect(gs,(200,200,255,18),(0,0,32,rb-rt))
        surf.blit(gs,(px-16,rt),special_flags=pygame.BLEND_RGBA_ADD)
        glow_circ(surf,(220,210,255),(px,rt),35,55)
        pygame.draw.circle(surf,(230,220,255),(px,rt),5)
    # Ground glow strip
    for thick,al,col in [(16,25,(110,70,240)),(7,70,(150,110,240)),(2,180,WHITE)]:
        gs=pygame.Surface((w,thick),pygame.SRCALPHA)
        pygame.draw.line(gs,(*col,al),(0,thick//2),(w,thick//2),thick)
        surf.blit(gs,(0,ground-thick//2),special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.line(surf,GOLD,(0,ground),(w,ground),2)
    # Floor reflective sheen
    fl=pygame.Surface((w,int(h*.22)),pygame.SRCALPHA)
    for fy in range(0,int(h*.22),3):
        fa=int(8*(1-fy/(h*.22)))
        pygame.draw.line(fl,(120,100,200,fa),(0,fy),(w,fy))
    surf.blit(fl,(0,ground),special_flags=pygame.BLEND_RGBA_ADD)

# ═══════════════════════════════════════════════════════════════════════════
#  HUD
# ═══════════════════════════════════════════════════════════════════════════
def draw_hud(surf,w,h,player,bot,rnd,timer_f,t):
    bw=int(w*.33); bh=max(16,int(h*.030)); by=int(h*.046)
    pan=pygame.Surface((w,int(h*.125)),pygame.SRCALPHA)
    pygame.draw.rect(pan,(0,0,0,170),(0,0,w,int(h*.125)))
    surf.blit(pan,(0,0))
    _hbar(surf,int(w*.04),by,bw,bh,player.health,player.glow,player.glow2,"PLAYER",True,t)
    _sebar(surf,int(w*.04),by+bh+5,bw,player.shadow_energy,player.glow)
    _hbar(surf,int(w*.63),by,bw,bh,bot.health,   bot.glow,  bot.glow2,"BOT",   False,t)
    _sebar(surf,int(w*.63),by+bh+5,bw,bot.shadow_energy,bot.glow)
    # centre
    cx=w//2; secs=max(0,timer_f//60)
    tc=RED_HIT if secs<10 else WHITE
    txt(surf,f"{secs:02d}",cx,by,tc,Flg,"midtop")
    txt(surf,f"ROUND {rnd:02d}",cx,by+bh+8,GREY,Fsm,"midtop")
    pulse=.5+.5*math.sin(t*.005)
    txt(surf,"VS",cx,by-5,(int(GREY[0]*pulse),int(GREY[1]*pulse),int(GREY[2]*pulse)),Fsm,"midbottom")
    txt(surf,"SHADOW-BOXER",cx,int(h*.007),GOLD,Flg,"midtop")
    # combo
    if player.combo>1:
        cp=.5+.5*math.sin(t*.01)
        cc=(int(GOLD[0]*cp+P_GLOW[0]*(1-cp)),int(GOLD[1]*cp+P_GLOW[1]*(1-cp)),int(GOLD[2]*cp))
        txt(surf,f"⚡ COMBO ×{player.combo}",int(w*.04),int(h*.88),cc,Fmd)
    if player.shadow_energy>=50:
        sm_a=int(128+127*math.sin(t*.008))
        s_surf=Fsm.render("◆ SHADOW MODE READY ◆",True,(*P_GLOW,sm_a))
        surf.blit(s_surf,(int(w*.04),int(h*.92)))
    # crouch indicator
    if player.state in (Fighter.DUCK,Fighter.SWEEP):
        txt(surf,"▼ CROUCHING",int(w*.04),int(h*.82),P_GLOW2,Fxs)
    # cam dot
    if WEBCAM_AVAILABLE:
        c=GREEN if _cam_active else GREY
        glow_circ(surf,c,(w-22,20),12,80); pygame.draw.circle(surf,c,(w-22,20),5)
        txt(surf,"CAM",w-65,12,c,Fxs)

def _hbar(surf,x,y,w,h,hp,ch,ch2,lbl,left,t):
    pygame.draw.rect(surf,(14,10,28),(x,y,w,h),border_radius=5)
    fill=int(w*max(0,hp)/100)
    if fill>0:
        gc=ch if hp>50 else (GOLD if hp>25 else RED_HIT)
        pygame.draw.rect(surf,gc,(x,y,fill,h),border_radius=5)
        shine=pygame.Surface((fill,h//2),pygame.SRCALPHA)
        pygame.draw.rect(shine,(255,255,255,22),(0,0,fill,h//2),border_radius=5)
        surf.blit(shine,(x,y))
        gs=pygame.Surface((10,h),pygame.SRCALPHA)
        pygame.draw.rect(gs,(*gc,170),(0,0,10,h)); surf.blit(gs,(x+fill-5,y),special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.rect(surf,(80,80,120),(x,y,w,h),2,border_radius=5)
    lx=x if left else x+w; anc="topleft" if left else "topright"
    txt(surf,lbl,lx,y-23,WHITE,Fhud,anc)
    txt(surf,str(max(0,hp)),x+w//2,y,WHITE,Fxs,"midtop")

def _sebar(surf,x,y,w,hp,col):
    pygame.draw.rect(surf,(14,10,28),(x,y,w,4),border_radius=2)
    fill=int(w*hp/100)
    if fill>0:
        pygame.draw.rect(surf,col,(x,y,fill,4),border_radius=2)
        gs=pygame.Surface((fill,4),pygame.SRCALPHA)
        pygame.draw.rect(gs,(*col,80),(0,0,fill,4),border_radius=2)
        surf.blit(gs,(x,y),special_flags=pygame.BLEND_RGBA_ADD)

# ═══════════════════════════════════════════════════════════════════════════
#  SCREENS
# ═══════════════════════════════════════════════════════════════════════════
def draw_intro(surf,w,h,t):
    vig=pygame.Surface((w,h),pygame.SRCALPHA)
    for r in range(max(w,h)//2,0,-4):
        a=int(55*(1-r/(max(w,h)/2))**2)
        pygame.draw.circle(vig,(0,0,0,a),(w//2,h//2),r)
    surf.blit(vig,(0,0))

    p=.5+.5*math.sin(t*.003)
    gc=(int(GOLD[0]*p),int(GOLD[1]*p),int(GOLD[2]*p))

    glow_circ(surf,GOLD,(w//2,int(h*.30)),200,int(60*p))
    txt(surf,"SHADOW-BOXER",w//2,int(h*.26),gc,Fxl,"center")
    txt(surf,"SHADOW FIGHT  4  EDITION",w//2,int(h*.42),WHITE,Flg,"center")

    for lx in range(int(w*.3),int(w*.7),4):
        a=int(255*(1-abs(lx-w//2)/(w*.2))**2)
        pygame.draw.line(
            surf,(*GOLD,a),
            (lx,int(h*.52)),
            (lx,int(h*.52)+1),
            2
        )

    # Webcam and gesture instructions
    if WEBCAM_AVAILABLE:
        txt(surf,"◉  WEBCAM GESTURES ENABLED",
            w//2,int(h*.56),GREEN,Fsm,"center")

        txt(surf,"LEAN = MOVE   BOTH HANDS UP = JUMP   CROUCH = DUCK   RIGHT ARM EXTEND = PUNCH   LEFT ARM NEAR CHIN = BLOCK",
            w//2,int(h*.61),WHITE,Fxs,"center")

        txt(surf,"STAND UPRIGHT + PRESS C TO CALIBRATE",
            w//2,int(h*.66),GOLD,Fxs,"center")
    else:
        txt(surf,"Keyboard controls active  (no webcam libs found)",
            w//2,int(h*.57),GREY,Fsm,"center")

    # Keyboard instructions
    txt(surf,"A/D = MOVE   W = JUMP   S = DUCK   Q = PUNCH   E = BLOCK",
        w//2,int(h*.72),GREY,Fxs,"center")

    txt(surf,"Crouch + Q = SWEEP KICK (hits crouching opponents!)",
        w//2,int(h*.77),P_GLOW2,Fxs,"center")

    # Start instruction
    blink=int(255*abs(math.sin(t*.004)))

    txt(surf,"▶  PRESS ENTER TO START  ◀",
        w//2,int(h*.83),(blink,blink,blink),Fmd,"center")

    # Additional controls
    txt(surf,"ESC = Quit   F2 = Webcam overlay   F3 = On-screen buttons",
        w//2,int(h*.92),GREY,Fxs,"center")
def draw_ko(surf,w,h,winner,t):
    ov=pygame.Surface((w,h),pygame.SRCALPHA); ov.fill((0,0,0,170)); surf.blit(ov,(0,0))
    p=.5+.5*math.sin(t*.005)
    kc=(min(255,int(255*p)),int(30*p),int(30*p))
    glow_circ(surf,kc,(w//2,int(h*.35)),130,int(130*p))
    txt(surf,"K · O",w//2,int(h*.26),kc,Fxl,"center")
    txt(surf,f"{winner} WINS!",w//2,int(h*.46),GOLD,Flg,"center")
    txt(surf,"ENTER = play again    ESC = quit",w//2,int(h*.62),WHITE,Fmd,"center")

def draw_webcam(surf,frame_bgr,w,h):
    if frame_bgr is None: return
    rgb=frame_bgr[:,:,::-1]; pw=int(w*.20); ph=int(pw*.75)
    try:
        small=cv2.resize(rgb,(pw,ph))
        fs=pygame.surfarray.make_surface(np.transpose(small,(1,0,2)))
        pan=pygame.Surface((pw+8,ph+28),pygame.SRCALPHA)
        pygame.draw.rect(pan,(0,0,0,160),(0,0,pw+8,ph+28),border_radius=8)
        surf.blit(pan,(w-pw-14,h-ph-32))
        surf.blit(fs,(w-pw-10,h-ph-10))
        pygame.draw.rect(surf,P_GLOW,(w-pw-10,h-ph-10,pw,ph),2)
        txt(surf,"WEBCAM",w-pw-10,h-ph-26,GREEN,Fxs)
    except: pass

# ═══════════════════════════════════════════════════════════════════════════
#  LAYOUT & BUTTONS
# ═══════════════════════════════════════════════════════════════════════════
def get_layout(sc):
    w,h=sc.get_size(); g=int(h*.78); fh=int(h*.27); fw=int(fh*.52)
    return {"width":w,"height":h,"ground":g,"fw":fw,"fh":fh,
            "speed":max(4,w*.005),"jump_v":-h*.028,"gravity":h*.0013}

def get_btns(w,h):
    bs=int(min(h*.10,w*.08)); gap=int(bs*.14); bot_=h-bs-int(h*.03)
    return {"LEFT":pygame.Rect(int(w*.03),bot_,bs,bs),
            "RIGHT":pygame.Rect(int(w*.03)+bs+gap,bot_,bs,bs),
            "JUMP":pygame.Rect(w-int(w*.03)-bs,bot_-bs-gap,bs,bs),
            "DUCK":pygame.Rect(w-int(w*.03)-bs,bot_,bs,bs),
            "PUNCH":pygame.Rect(w-int(w*.03)-bs*2-gap,bot_-bs-gap,bs,bs),
            "BLOCK":pygame.Rect(w-int(w*.03)-bs*2-gap,bot_,bs,bs)}

def draw_btns(surf,buttons):
    labels={"LEFT":"◄","RIGHT":"►","JUMP":"▲","DUCK":"▼","PUNCH":"Q","BLOCK":"E"}
    cols={"PUNCH":P_GLOW,"BLOCK":B_GLOW,"JUMP":GOLD,"DUCK":PURPLE}
    for act,rect in buttons.items():
        bc=cols.get(act,(60,80,160))
        s=pygame.Surface(rect.size,pygame.SRCALPHA); s.fill((*bc,110))
        surf.blit(s,rect.topleft)
        pygame.draw.rect(surf,(*bc,200),rect,2,border_radius=10)
        txt(surf,labels[act],rect.centerx,rect.centery,WHITE,Fsm,"center",shd=False)

def new_round(L):
    w=L["width"]
    p=Fighter(w*.20,+1,P_GLOW,P_GLOW2,P_CORE,"PLAYER",True)
    b=Fighter(w*.72,-1,B_GLOW,B_GLOW2,B_CORE,"BOT",   False)
    return p, b, BotAI(b)

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════
_cam_active=False; pose_tracker=None
if WEBCAM_AVAILABLE:
    pose_tracker=PoseTracker(); _cam_active=pose_tracker.start()

INTRO="intro"; PLAY="play"; KO="ko"
gstate=INTRO; rnd=1; RF=99*60; rtimer=RF; winner=""
parts=Particles(); shake=Shake()
layout=get_layout(screen)
player,bot,bot_ai=new_round(layout)

kbd=set(); touch=set(); mouse_btn=None
show_web=True; show_btns=IS_MOBILE
render=pygame.Surface(screen.get_size())

# ember spawn timers
_ember_timer=0

running=True
while running:
    t=pygame.time.get_ticks(); dt=min(clock.tick(60)/16.67,2.5)
    layout=get_layout(screen); W,H=layout["width"],layout["height"]
    buttons=get_btns(W,H)
    if render.get_size()!=(W,H): render=pygame.Surface((W,H))

    for ev in pygame.event.get():
        if ev.type==pygame.QUIT: running=False
        elif ev.type==pygame.VIDEORESIZE and not IS_MOBILE:
            screen=pygame.display.set_mode((max(640,ev.w),max(400,ev.h)),pygame.RESIZABLE)
        elif ev.type==pygame.KEYDOWN:
            k=ev.key
            if k==pygame.K_ESCAPE: running=False
            elif k==pygame.K_F2: show_web=not show_web
            elif k==pygame.K_F3: show_btns=not show_btns
            elif k in (pygame.K_RETURN,pygame.K_KP_ENTER):
                if gstate in (INTRO,KO):
                    layout=get_layout(screen)
                    player,bot,bot_ai=new_round(layout)
                    rtimer=RF; parts.p.clear(); parts.trails.clear()
                    parts.dmg.clear(); _shockwaves.clear(); _bg_cache.clear(); _gcache.clear()
                    gstate=PLAY
            if k in (pygame.K_a,pygame.K_LEFT):              kbd.add("LEFT")
            if k in (pygame.K_d,pygame.K_RIGHT):             kbd.add("RIGHT")
            if k in (pygame.K_w,pygame.K_UP,pygame.K_SPACE): kbd.add("JUMP")
            if k in (pygame.K_s,pygame.K_DOWN):              kbd.add("DUCK")
            if k==pygame.K_q:                                kbd.add("PUNCH")
            if k==pygame.K_e:                                kbd.add("BLOCK")
            if k == pygame.K_c and pose_tracker and _cam_active:
                pose_tracker.request_calibration()
        elif ev.type==pygame.KEYUP:
            km={pygame.K_a:"LEFT",pygame.K_LEFT:"LEFT",pygame.K_d:"RIGHT",pygame.K_RIGHT:"RIGHT",
                pygame.K_w:"JUMP",pygame.K_UP:"JUMP",pygame.K_SPACE:"JUMP",
                pygame.K_s:"DUCK",pygame.K_DOWN:"DUCK",pygame.K_q:"PUNCH",pygame.K_e:"BLOCK"}
            if ev.key in km: kbd.discard(km[ev.key])
        elif ev.type==pygame.FINGERDOWN:
            pos=(int(ev.x*W),int(ev.y*H))
            for a,r in buttons.items():
                if r.collidepoint(pos): touch.add(a)
            if gstate==INTRO: gstate=PLAY
        elif ev.type==pygame.FINGERUP: touch.clear()
        elif ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            if show_btns:
                for a,r in buttons.items():
                    if r.collidepoint(ev.pos): mouse_btn=a
            if gstate==INTRO: gstate=PLAY
        elif ev.type==pygame.MOUSEBUTTONUP and ev.button==1:
            mouse_btn=None

    pa=set(kbd)|set(touch)
    if mouse_btn: pa.add(mouse_btn)
    if pose_tracker and _cam_active:
        can_punch = (
            gstate == PLAY
            and player.state not in (Fighter.HIT, Fighter.KO)
            and player.punch_timer == 0
        )
        pa |= pose_tracker.get_actions(accept_punch=can_punch)

    if gstate==PLAY:
        rtimer=max(0,rtimer-1)
        player.update(layout,pa,bot,parts,shake,dt)
        ba=bot_ai.acts(player,layout,t)
        bot.update(layout,ba,player,parts,shake,dt)
        # spawn atmospheric embers
        _ember_timer+=1
        if _ember_timer%12==0:
            parts.spawn_ember(W,H,random.choice([P_GLOW,B_GLOW,GOLD]))
        if player.health<=0:   winner=bot.name;    gstate=KO
        elif bot.health<=0:    winner=player.name; gstate=KO
        elif rtimer==0:        winner=player.name if player.health>=bot.health else bot.name; gstate=KO

    # ── render ─────────────────────────────────────────────────────────
    rs=render
    draw_bg(rs,W,H,t)
    draw_arena(rs,W,H,layout["ground"])
    draw_sw(rs)

    if gstate==INTRO:
        draw_intro(rs,W,H,t)
    elif gstate in (PLAY,KO):
        # draw back-fighter first (depth sort)
        if player.x<bot.x: player.draw(rs,layout); bot.draw(rs,layout)
        else:               bot.draw(rs,layout);    player.draw(rs,layout)
        parts.update_draw(rs)
        draw_hud(rs,W,H,player,bot,rnd,rtimer,t)
        if gstate==KO: draw_ko(rs,W,H,winner,t)

    if show_btns or IS_MOBILE: draw_btns(rs,buttons)
    if show_web and pose_tracker and _cam_active:
        frame=pose_tracker.get_frame(); draw_webcam(rs,frame,W,H)
    if pose_tracker and _cam_active:
        cam_status, cam_calibrated = pose_tracker.get_status()

        status_color = GREEN if cam_calibrated else GOLD

        txt(
            rs,
            f"GESTURE: {cam_status}",
            12,
            H - 28,
            status_color,
            Fgesture
        )

    ox,oy=shake.off()
    screen.fill(C_BLACK); screen.blit(rs,(ox,oy))
    pygame.display.flip()

if pose_tracker: pose_tracker.stop()
pygame.quit(); sys.exit()

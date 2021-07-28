import eel,math,pyglet,time,threading,random
from pyglet.gl import *
from pyglet.window import *
from pyglet import image
from opensimplex import OpenSimplex

tmp = OpenSimplex()

FACES=[(0,1,0),(0,-1,0),(-1,0,0),(1,0,0),(0,0,1),(0,0,-1),(0,0,0)]
TEX=0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,1,0,0,1,0,1,1,0,1
CURRENTBLOCK = "dirt"
TEXTURES = {}

BLOCKS = {
    "dirt":"dirt.png",
    "grass":"grass_top.png",
    "stone":"stone.png",
    "wood": "wood.png",
    "leaf": "leaf.png",
    "water": "water.png",
}

@eel.expose
def say_hello_py(block):
    global CURRENTBLOCK
    CURRENTBLOCK = block

def normalize(pos):
    x,y,z = pos
    return round(x), round(y), round(z)

def new_crosshair(w,h):
    return pyglet.text.Label('+',font_name='Times New Roman',font_size=36,x=w/2,y=h/2)

def get_tex(f):
    d = BLOCKS[f]
    TEXTURES[f] = pyglet.graphics.TextureGroup(pyglet.image.load("./textures/"+d).get_texture())
    glEnable(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

def cube_vertices(pos, n=.5):
    x,y,z = pos
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]

class World:
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        self._shown = {}
        self.blocks = {}
        self.chunks = set()

    def add_block(self,pos,id):
        self.blocks[pos] = id
        self.show_block(pos,id)
        self.check_neighbors(pos)

    def del_block(self,pos):
        self.blocks.pop(pos)
        self._shown.pop(pos).delete()
        self.check_neighbors(pos)

    def show_block(self,pos,block_type):
        try:
            self._shown[pos] = self.batch.add(24, GL_QUADS, TEXTURES[block_type],('v3f/static', cube_vertices(pos)),('t2f/static', TEX))
        except Exception as e:
            print(e)
            get_tex(block_type)
            print("getting tex",block_type)
            self.show_block(pos,block_type)
    
    def hide_block(self,pos):
        self._shown.pop(pos).delete()

    def hit_test(self, pos, vector,m=8):
        dx, dy, dz = vector
        previous = None
        for _ in range(m*4):
            x,y,z = pos
            block = normalize(pos)
            if block != previous and block in self._shown:
                return block, previous
            previous = block
            pos = x + dx / m, y + dy / m, z + dz / m
        return None, None

    def check_neighbors(self, pos):
        x,y,z = pos
        for dx, dy, dz in FACES:
            block = (x + dx, y + dy, z + dz)
            if block not in self.blocks: continue
            elif self.exposed(block):
                if block not in self._shown:
                    self.show_block(block,self.blocks[block])
            elif block in self._shown: self.hide_block(block)

    def exposed(self, pos):
        x,y,z = pos
        for dx, dy, dz in FACES:
            if (x + dx, y + dy, z + dz) not in self.blocks:
                return True
        return False

    def gen_chunk(self,pos):
        chunk_x = int(pos[0]/16)
        chunk_z = int(pos[2]/16)
        x,y,z = 0,0,0
        if (chunk_x,chunk_z) not in self.chunks:
            self.chunks.add((chunk_x,chunk_z))
            while z < 16:
                while x < 16:
                    y_max = 6 + int(((tmp.noise2d(chunk_x+x/16, chunk_z+z/16)+1)/2)*15)
                    while y < y_max:
                        if y == y_max-1: id = "grass"
                        elif y < 3: id = "stone"
                        else: id = "dirt"
                        self.add_block((chunk_x*16+x,y,chunk_z*16+z),id)
                        y += 1
                    # Set water level to y = 9
                    if y_max <= 9:
                        self.add_block((chunk_x*16+x,9,chunk_z*16+z),"water")
                    #trees
                    elif random.randrange(200) == 1:
                        self.add_block((chunk_x*16+x,y_max,chunk_z*16+z),"wood")
                        self.add_block((chunk_x*16+x,y_max+1,chunk_z*16+z),"wood")
                        self.add_block((chunk_x*16+x,y_max+2,chunk_z*16+z),"wood")
                        self.add_block((chunk_x*16+x,y_max+3,chunk_z*16+z),"leaf")
                        self.add_block((chunk_x*16+x+1,y_max+2,chunk_z*16+z),"leaf")
                        self.add_block((chunk_x*16+x-1,y_max+2,chunk_z*16+z),"leaf")
                        self.add_block((chunk_x*16+x,y_max+2,chunk_z*16+z+1),"leaf")
                        self.add_block((chunk_x*16+x,y_max+2,chunk_z*16+z-1),"leaf")
                    x += 1
                    y = 0 
                x = 0
                z += 1

class Player:
    def __init__(self, pos=(0, 0, 0), rot=(0, 0)):
        self.pos = list(pos)
        self.rot = list(rot)
        self.speed = .05

class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = True
        self.hud_position = self.width/2-364
        self.fps_display = pyglet.window.FPSDisplay(self)
        
        #Blits
        self.hud = image.load('./textures/hud.png')
        self.active = image.load('./textures/active.png')
        self.crosshair =  new_crosshair(self.width,self.height)
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.holding = "dirt"
        self.hud_offset = 0
        self.world = World()
        #I put the player at 10K,10K because of a chunkgen bug at x=0 and z=0
        self.player = Player((10000,12,10000),(-90,0))
        pyglet.clock.schedule(self.game_loop)

    def push(self):
        glPushMatrix()
        rot = self.player.rot
        x,y,z = self.player.pos
        glRotatef(-rot[0],1,0,0)
        glRotatef(-rot[1],0,1,0)
        glTranslatef(-x, -y, -z)

    def clean(self):
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

    def set3d(self):
        self.clean()
        gluPerspective(70, self.width/self.height, 0.05, 1000)
        glMatrixMode(GL_MODELVIEW)
    
    def set2d(self):
        self.clean()
        glOrtho(0, float(self.width),0, float(self.height), 0, 1)
        glMatrixMode(GL_MODELVIEW)

    def on_mouse_motion(self,x,y,dx,dy):
        if self.lock:
            rot = self.player.rot
            rot[0] += dy/8
            rot[1] -= dx/8
            if rot[0]>90: rot[0] = 90
            elif rot[0] < -90: rot[0] = -90

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if (scroll_y > 0): self.set_active(-80)
        else: self.set_active(80)

    def on_mouse_press(self, x, y, button, pos):
        hit,previous = self.world.hit_test(self.player.pos,self.sight_vector(self.player))
        if button == 4 and previous:
            global CURRENTBLOCK
            if self.holding == 0: CURRENTBLOCK = "dirt"
            if self.holding == 1: CURRENTBLOCK = "grass"
            if self.holding == 2: CURRENTBLOCK = "wood"
            if self.holding == 3: CURRENTBLOCK = "leaf"
            if self.holding == 4: CURRENTBLOCK = "stone"
            self.world.add_block(previous,CURRENTBLOCK)
        elif button == 1 and hit: self.world.del_block(hit)

    def on_key_press(self, KEY, _MOD):
        if KEY == key.ESCAPE: self.close()
        if KEY == key.E: self.lock = not self.lock; self.set_exclusive_mouse(self.lock)
        if KEY == key.M: eel.init('web'); eel.start('craft.html')
    
    def gen_rad_chunks(self,pos):
        x,y,z = normalize(pos)
        points = {
            (0,0,0),
            (16,0,0),
            (-16,0,0),
            (0,0,16),
            (0,0,-16),
            (16,0,16),
            (-16,0,16),
            (-16,0,-16),
            (16,0,-16),
        }
        for point in points:
            x_,y_,z_ = point
            self.world.gen_chunk((x+x_,y_,z+z_))
            

    def player_movement(self):
        rotY = -self.player.rot[1]/180*math.pi
        dx, dz = math.sin(rotY), math.cos(rotY)
        keys = self.keys
        pos = self.player.pos
        s = self.player.speed
        if keys[key.W]: pos[0] += dx*s; pos[2] -= dz*s
        if keys[key.S]: pos[0] -= dx*s; pos[2] += dz*s
        if keys[key.A]: pos[0] -= dz*s; pos[2] -= dx*s
        if keys[key.D]: pos[0] += dz*s; pos[2] += dx*s
        if keys[key.SPACE]: pos[1] += s
        if keys[key.LSHIFT]: pos[1] -= s

    def sight_vector(self,player):
        y,x = player.rot
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(-x - 90)) * m
        dz = math.sin(math.radians(-x - 90)) * m
        return (dx, dy, dz)

    def set_active(self,move):
        self.hud_offset += move 
        if (self.hud_offset > 650): self.hud_offset = 0
        elif (self.hud_offset < 0): self.hud_offset = 640
        self.holding = int(self.hud_offset/80)

    def draw_focused_block(self):
        block = self.world.hit_test(self.player.pos, self.sight_vector(self.player))[0]
        if block:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f', cube_vertices(block)))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def game_loop(self,dt):
        self.player_movement()
        self.gen_rad_chunks(self.player.pos)
    
    def draw_hud(self):
        self.crosshair.draw()
        self.active.blit(self.hud_position+self.hud_offset, 0, 0) #Front
        self.hud.blit(self.hud_position, 0, 0)                    #HUD

    def on_draw(self):
        self.clear()
        self.set3d()
        self.push()
        self.world.batch.draw()
        self.draw_focused_block()
        self.set2d()
        self.draw_hud()
        self.fps_display.draw()
        glPopMatrix()

if __name__ == '__main__':
    window = Window(1280,720, caption='Cropcraft', vsync=True, resizable=True)

    @window.event
    def on_resize(width, height):
        window.crosshair = new_crosshair(width,height)
        window.hud_position = width/2-364
    
    #Face Culling
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glFrontFace(GL_CCW)
    
    #FOG
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
    glHint(GL_FOG_HINT, GL_FASTEST)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 10.0)
    glFogf(GL_FOG_END, 24.0)

    #Skybox/Void color
    glClearColor(0.5, 0.69, 1.0, 1)
    
    pyglet.app.run()
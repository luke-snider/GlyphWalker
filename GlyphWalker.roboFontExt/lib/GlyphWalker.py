#coding=utf-8
from __future__ import print_function, division, absolute_import
'''
v.0.5 - 06/2020
Lukas Schneider - Revolver Type Foundry - www.revolvertype.com
GlyphWalker lets you walk trough a glyph simultaneously back and forth in all open fonts.
the tool takes the user setting (short cut) for next/previous glyph from the user preferences!

move to next/previous glyph with your regular shortcut (RF preferences)

Reorder open fonts according to family, width, weight is based on a script by Dan Milne.
'''
from vanilla import *
from mojo.UI import *
from AppKit import *
from vanilla.dialogs import getFile, putFile, message
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.events import addObserver,removeObserver


class GlyphWalker(BaseWindowController):

    def __init__(self):

        widtOfTool = 115
        self.w = FloatingWindow((widtOfTool, 165), '') 

        y = 5
        self.w.tabGlyphsButton = Button((5, y, -5, 18), title="Display settings", sizeStyle = "mini", callback=self.toggleOptions)

        self.w.hLine1 = HorizontalLine((0, y+20, 0, 10))
        self.w.hLine1a = HorizontalLine((0, y+21, 0, 10))
        self.scales = ["Fit window size","current scale size"]
        self.w.scalePopup = PopUpButton((5,y+30,-5,20), self.scales, sizeStyle = "mini")
        self.w.scaleMinus = Button((5,y+50,50,25), "+", callback=self.scale, sizeStyle="regular")
        self.w.scalePlus = Button((60,y+50,50,25), "-", callback=self.scale, sizeStyle="regular")
        self.w.hLine2 = HorizontalLine((0, y+75, 0, 10))
        self.w.hLine2a = HorizontalLine((0, y+76, 0, 10))
        self.w.btnX = SquareButton((5,y+88,-5,16), "Open current (all)", callback=self.openAllFontsGlyphWindows, sizeStyle="mini")
        self.w.tileButton = SquareButton((5,  y+108, -5, 15), "Tile glyph windows", sizeStyle="mini", callback=self.tile)
        self.w.hLine2b = HorizontalLine((0, y+125, 0, 10))
        self.w.glyphSelectionButton = SegmentedButton((5, -28, 120, 20), [dict(width=98, title="save all fonts")], sizeStyle="small", callback=self.saveAllFonts)
        self.w.glyphSelectionButton.set(0)

        y2 = -12
        self.popOver = Popover((150, 440), parentView=self.w, preferredEdge='right', behavior="applicationDefined")        
        self._popOverIsVisible = False

        y_checkBox = 10 
        for displayOption, trueOrFalse in sorted(getGlyphViewDisplaySettings().items()):
            x = 10
            checkBox = CheckBox((x, y_checkBox, -5, 15), displayOption, value=trueOrFalse, sizeStyle="small", callback=self.editCheckboxDisplaySettings)
            setattr(self.popOver, displayOption, checkBox)
            y_checkBox += 15
        self.popOver.layerTransparencyTxt = TextBox((x, y_checkBox+10, -5, 25),text="LAYER TRANSPARENCY", sizeStyle="small")
        self.popOver.layerTransparency = Slider((x,y_checkBox+25,-10,20), value=0, tickMarkCount=10, stopOnTickMarks=True, sizeStyle='mini', minValue=0, maxValue=100, callback=self.layerTransparency)

        self.setUpBaseWindowBehavior()
        addObserver(self, "keyWasPressed", "keyDown")
        addObserver(self, "keyWasPressed", "keyDownWithoutModifiers")

        self.ordered_open = []
        self.w.open()

    def editCheckboxDisplaySettings(self, sender):
        checkboxTitle = sender.getTitle()
        checkboxValue = sender.get()
        if checkboxValue == 1: setGlyphViewDisplaySettings({checkboxTitle:True})
        else: setGlyphViewDisplaySettings({checkboxTitle:False})

    def layerTransparency(self, sender):
        value = int(round(sender.get()))
        if AllFonts() != None: 
            for f in AllFonts():
                for layername in f.layerOrder:
                    f.setLayerDisplay(layername, 'Fill', value)
                    f.setLayerDisplay(layername, 'Stroke', value)


    def windowCloseCallback(self, sender):
        removeObserver(self, "keyDown")
        removeObserver(self, "keyDownWithoutModifiers")
        super(GlyphWalker, self).windowCloseCallback(sender)


    def toggleOptions(self, sender):
        if self._popOverIsVisible:
            self.popOver.close()
            self._popOverIsVisible = False
            sender.setTitle("display settings")
        else:
            self.popOver.open(parentView=sender)
            self._popOverIsVisible = True
            sender.setTitle("close settings")
            sender.enable(True)


    def orderAllOpenFonts(self):
        allopen = AllFonts()
        unordered = []
        for i in range(len(allopen)):
            family = allopen[i].info.familyName
            if allopen[i].info.italicAngle is not None:
                slope = abs(allopen[i].info.italicAngle)
            else:
                slope = 0
        
            weight = allopen[i].info.openTypeOS2WeightClass
            if weight == None:
                print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                print('OpenType weight class is not defined in ' + str(family) + '. Order may be incorrect.')
                print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                weight = 0
                
            width = allopen[i].info.openTypeOS2WidthClass
            if width == None:
                print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                print('OpenType width class is not defined in ' + str(family) + '. Order may be incorrect.')
                print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                width = 0
            unordered.append((i,family,slope,width,weight))

        ordered_weight = sorted(unordered, key=lambda tup: tup[4]) # reverse sort on weight
        ordered_width = sorted(ordered_weight, key=lambda tup: tup[3]) # reverse sort on width
        ordered_slope = sorted(ordered_width, key=lambda tup: tup[2]) # reverse sort on slope
        ordered_family = sorted(ordered_slope, key=lambda tup: tup[1]) # reverse sort on weight

        self.ordered_open = []
        for item in reversed(ordered_family):
            self.ordered_open.append(allopen[item[0]])

            
    def openAllFontsGlyphWindows(self, sender):
        if CurrentGlyphWindow() == None:
            if CurrentFont() == None:
                message("Open font(s) first!")
            else:
                message("Open a glyph window first!")
        else:
            self.orderAllOpenFonts()
            if CurrentGlyph() !=None:
                glyphName = CurrentGlyph().name
                for font in self.ordered_open:
                    if font.has_key(glyphName):
                        OpenGlyphWindow(font[glyphName])
                    else:
                        message("Glyph not in all fonts!")
                        return
                for glyphwin in AllGlyphWindows():
                    try:
                        currentScale = glyphwin.getGlyphViewScale()
                        glyphwin.setGlyphViewScale(currentScale-0.1)
                        glyphwin.centerGlyphInView()
                    except TypeError:
                        pass  

    def scale(self, sender):
        title = sender.getTitle()
        if title == "+":
            if CurrentGlyph() != None:
                for glyphwin in AllGlyphWindows():
                    try:
                        currentScale = glyphwin.getGlyphViewScale()
                        glyphwin.setGlyphViewScale(currentScale+0.1)
                        glyphwin.centerGlyphInView()
                    except TypeError:
                        pass            
        if title == "-":
            if CurrentGlyph() != None:
                for glyphwin in AllGlyphWindows():
                    try:
                        currentScale = glyphwin.getGlyphViewScale()
                        glyphwin.setGlyphViewScale(currentScale-0.1)
                        glyphwin.centerGlyphInView()
                    except TypeError:
                        pass  


    def keyWasPressed(self, info):
        nextGlyph = exportPreferences(path=None)["glyphViewNextGlyphKey"]
        previousGlyph = exportPreferences(path=None)["glyphViewPreviousGlyphKey"]
        
        event = info["event"]
        characters = event.characters()
        #print("characters",characters)
        if characters == nextGlyph:
            #print("nextGlyph", nextGlyph)
            moveForwardOrBackwards = "nextGlyph"
            self.walk(moveForwardOrBackwards)
        if characters == previousGlyph:
            #print("previousGlyph", previousGlyph)
            moveForwardOrBackwards = "previousGlyph"
            self.walk(moveForwardOrBackwards)


    def walk(self, moveForwardOrBackwards):
        font = CurrentFont()
        if CurrentGlyph() != None:
            glyphname = CurrentGlyph().name
            glyphOrder = font.glyphOrder
            if len(glyphOrder) != 0:

                for i, name in enumerate(glyphOrder):
                    if name == glyphname:
                        try:
                            theGlyphNameBefore = glyphOrder[i-1]
                            theGlyphNameAfter = glyphOrder[i+1]
                        except IndexError:
                            ### last glyph in order
                            theGlyphNameAfter = glyphOrder[0]
                            theGlyphNameBefore = glyphOrder[i-1]

                if moveForwardOrBackwards == "previousGlyph":
                    theGlyphName = theGlyphNameBefore
                if moveForwardOrBackwards == "nextGlyph":
                    theGlyphName = theGlyphNameAfter
       
                collectedScales = []
                for i, glyphwin in enumerate(reversed(AllGlyphWindows())): 
                    if i == len(AllGlyphWindows())-1:
                        try:
                            theGlyphName = glyphwin.getGlyph()
                            scale = self.getGlyphWidthHeight(glyphwin, theGlyphName)
                            collectedScales.append(scale)              
                        except TypeError:
                            pass
                    else:
                        try:
                            glyphwin.setGlyphByName(theGlyphName)
                            glyph = glyphwin.getGlyph()
                            scale = self.getGlyphWidthHeight(glyphwin, glyph)
                            collectedScales.append(scale)              
                        except TypeError:
                            pass
                if collectedScales != None:
                    scale = max(collectedScales)
                else:
                    scale == 0.7
                if self.w.scalePopup.get() == 0:
                    scale = scale
                if self.w.scalePopup.get() == 1:
                    scale = CurrentGlyphWindow().getGlyphViewScale()
                
                for glyphwin in reversed(AllGlyphWindows()):   
                    try:
                        glyphwin.setGlyphByName(theGlyphName)
                        glyphwin.setGlyphViewScale(scale)
                        glyphwin.centerGlyphInView()                    
                    except TypeError:
                        pass


    def getGlyphWidthHeight(self, glyphwin, glyph):
        if glyph.bounds:
            left, bottom, right, top = glyph.bounds
        else:
            left = right = bottom = top = 0
        visibleHeight = glyphwin.getVisibleRect()[-1]
        newHeight = (top-bottom)+60
        scale = visibleHeight / newHeight
        return scale


    def tile(self, sender):
        windows = [w for w in NSApp().orderedWindows() if w.isVisible()]
        screen = NSScreen.mainScreen()
        (x, y), (w, h) = screen.visibleFrame()
        altDown = NSEvent.modifierFlags() & NSAlternateKeyMask
        NSApp().arrangeInFront_(None)
        windowsToHide = []
        windowsToTile = []
        for window in windows:
            if hasattr(window, "windowName") and window.windowName() == "GlyphWindow":
                windowsToTile.append(window)
            else:
                windowsToHide.append(window)
                break

        tileInfo = {
                    1 : [[1]],
                    2 : [[],[1, 1]],
                    3 : [[],[1, 1, 1]],
                    4 : [[], [1, 1, 1, 1]],
                    5 : [[1, 1], [1, 1, 1]],
                    6 : [[1, 1, 1], [1, 1, 1]],
                    7 : [[1, 1, 1], [1, 1, 1, 1]],
                    8 : [[1, 1, 1, 1], [1, 1, 1, 1]],
                    9 : [[1, 1, 1, 1], [1, 1, 1, 1, 1]],
                    10 : [[1, 1, 1, 1, 1], [1, 1, 1, 1, 1]],
                    11 : [[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1]],
                    12 : [[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1]],
                    13 : [[1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1]],
                    14 : [[1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1]],
                    15 : [[1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1]],
                    16 : [[1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1]],
                    17 : [[1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1]],
                    18 : [[1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1]],
                    19 : [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1]],
                    20 : [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]],
                    }

        if windowsToTile:
            arrangement = tileInfo[len(windowsToTile)]
            maxHeight = len(arrangement)
            diffx = x
            diffy = y
            c = 0
            for i in arrangement:
                maxWidth = len(i)        
                for j in i:
                    window = windows[c]
                    window.setFrame_display_animate_(NSMakeRect(diffx, diffy, w/float(maxWidth), h/float(maxHeight)), True, altDown)
                    c += 1
                    diffx += w/float(maxWidth)
                diffx = x
                diffy += h/float(maxHeight)
        for window in windowsToHide:
            window.miniaturize_(None)

    def saveAllFonts(self, sender):
        for f in AllFonts():
            f = CurrentFont()
            try:
                f.save(path=None)
            except TypeError:
                f.save(destDir=None)

GlyphWalker()
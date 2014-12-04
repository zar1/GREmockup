#!/usr/bin/env python

import gtk, gobject
import gtk.glade
import os

APP_PATH = os.path.dirname(os.path.realpath(__file__))
     
class App:    
    
    class RadioGroup:
        def __init__(self, group, labels):
            self.__buttons = group.get_group()
            self.__labels = {}
            for index in xrange(len(self.__buttons)):
                self.__labels[self.__buttons[index]] = labels[index]
            self.__hidden = gtk.RadioButton()
            self.__hidden.set_group(group)
        def get_active_label(self):
            for button in self.__buttons:
                if button.get_active():
                    return self.__labels[button]
            return ''
        def clear(self):
            self.__hidden.set_active(True)  

    class Clock:
        def __init__(self, label, interval, timeOutHandler):
            self.__label = label
            # interval in ms
            self.__interval = interval
            self.__thisInterval = 0
            self.__ipers = int(1000/interval)
            # time in seconds
            self.__timeS = 0
            self.__hidden = False
            self.__tminus5 = True
            self.__inFlash = False
            self.__timeOutHandler = timeOutHandler
        def set_minutes(self, timeMin):
            # given time in minutes
            self.__timeS = timeMin * 60
            self.__thisInterval = 0
            self.__tminus5 = timeMin <= 5
        def hide(self):
            if not(self.__tminus5 or self.__hidden):
                self.__hidden = True
            else:
                self.__hidden = False
            self.__redraw()
        def tick(self):
            self.__thisInterval += 1
            if self.__thisInterval >= self.__ipers:
                self.__thisInterval = 0
                self.__timeS -= 1
                if self.__tminus5:
                    if self.__timeS <= 0:
                        self.__timeOutHandler()
                else:
                    if self.__timeS <= 300:
                        self.__tminus5 = True
                        self.__hidden = False
            self.__redraw()
            return True
        def __redraw(self):
            if self.__hidden:
                s = ''
            else:
                h = self.__timeS / 3600
                s = self.__timeS % 3600
                m = s / 60
                s = s % 60
                if self.__tminus5:
                    if self.__inFlash:
                        s = ''
                        self.__inFlash = False
                    else:
                        s = "%d:%d:%d" % (h, m, s)
                        self.__inFlash = True
                else:
                    s = "%d:%d" % (h, m)
            self.__label.set_text(s)
    class QCounter:
        def __init__(self, label, timeOutHandler):
            self.__label = label
            self.__timeOutHandler = timeOutHandler
            self.__q = 0
            self.__total = 0
        def set_questions(self, questions):
            self.__total = questions
            self.__q = 1
            self.__redraw()
        def tick(self):
            self.__q += 1
            if self.__q > self.__total:
                self.__timeOutHandler()
            else:
                self.__redraw()
        def __redraw(self):
            self.__label.set_text('Question %d of %d' % (self.__q, self.__total))
    def __init__(self):
        self.__next_pressed = False
        self.__answers = []
        #self.__tick = self.__fake_tick
        self.__init_gui()
        
    def __init_gui(self):
	
        self.__wTree = gtk.glade.XML(os.path.join(APP_PATH, 'form.glade'), 
		'mainWindow')
        
        signals = { 'on_buttonQuit_clicked' : self.__quit,
                    'on_buttonExit_clicked' : self.__exit,
                    'on_buttonTime_clicked' : self.__time,
                    'on_buttonHelp_clicked' : self.__help,
                    'on_buttonConfirm_clicked' : self.__confirm,
                    'on_buttonNext_clicked' : self.__next,
                    'on_radio_toggle' : self.__radioToggle}
        
        
        self.__wTree.signal_autoconnect(signals)
        
        self.__clock = self.Clock(self.__wTree.get_widget('labelTime'), 500, self.__timeOut)
        self.__labelTitle = self.__wTree.get_widget('labelTitle')
        self.__qCounter = self.QCounter(self.__wTree.get_widget('labelQuestion'), self.__timeOut)
        self.__radioGroup = self.RadioGroup(self.__wTree.get_widget('radiobuttonA'), ('E', 'D', 'C', 'B', 'A'))
        self.__radioGroup.clear()
        
        self.__buttonNext = self.__wTree.get_widget('buttonNext')
        self.__buttonConfirm = self.__wTree.get_widget('buttonConfirm')
        
        self.__w = self.__wTree.get_widget('mainWindow')
        
        self.__w.connect('destroy', lambda w: gtk.main_quit())
        
        self.__w.set_default_size(800, 640)
        #self.__w.fullscreen()
        self.__w.show() 
    def run(self):
        self.__start_test()
        gobject.timeout_add(500, self.__tick)
        
        gtk.main()   
    def __start_test(self):
        self.__next_pressed = False
        self.__answers = []
        instructions = self.__new_test_dialog()
        self.__labelTitle.set_text(instructions[0])
        self.__clock.set_minutes(instructions[1])
        self.__qCounter.set_questions(instructions[2])
        self.__buttonConfirm.set_sensitive(False)
        self.__ticker = self.Ticker(self.__clock.tick)
        self.__ticker.on()
    class Ticker:
        def __init__(self, function):
            self.__function = function
            self.run = self.__nop
        def __nop(self):
            return True
        def on(self):
            self.run = self.__function
        def off(self):
            self.run = self.__nop
    def __tick(self):
        self.__ticker.run()
        return True
    def __new_test_dialog(self):
        labels = (('GRE Quantitative Section', 45, 28), 
                  ('GRE Verbal Section', 30, 30))
        buttonVerbal = gtk.RadioButton()
        buttonVerbal.set_label('Verbal')
        buttonQuant = gtk.RadioButton()
        buttonQuant.set_label('Quantitative')
        buttonQuant.set_group(buttonVerbal)
        radioGroup = self.RadioGroup(buttonVerbal, labels)
        
        d = gtk.Dialog("Select Test Type", self.__w, gtk.DIALOG_DESTROY_WITH_PARENT,
                       (gtk.STOCK_OK, gtk.RESPONSE_OK))
        d.set_default_size(210,90)
        for b in (buttonVerbal, buttonQuant):
            d.vbox.pack_start(b)
            b.show()
        
        r = d.run()
        instruction = radioGroup.get_active_label()
        d.destroy()
        return instruction    
     
    def __timeOut(self):
        self.__ticker.off()
        #self.__tick = self.__fake_tick     
        self.__dump_answers()
        self.__start_test()
    def __dump_answers(self):
        sw = gtk.ScrolledWindow()
        tb = gtk.TextView()
        sw.add_with_viewport(tb)
        d = gtk.Dialog("You answered:", self.__w, gtk.DIALOG_DESTROY_WITH_PARENT,
                       (gtk.STOCK_OK, gtk.RESPONSE_OK))
        d.set_default_size(640, 480)
        d.vbox.pack_start(sw)
        tb.show()
        sw.show()
        s = ''
        i = 1
        for a in self.__answers:
            s = s + '%d : %s\n' % (i, a)
            i += 1
        tb.get_buffer().set_text(s)
        d.run()
        d.destroy()
    def __radioToggle(self, widget):
        if widget.state == 2:
            #we only care about the toggle on, not the toggle off
            #self.__buttonConfirm.set_sensitive(False)
            #self.__buttonNext.set_sensitive(True)
            pass
    def __quit(self, event):
        #self.__alert("WARNING: You pressed the quit button! Were this a real test, you're future would be ruined!")
        gtk.main_quit()
    def __alert(self, message):
        m = gtk.MessageDialog(parent=self.__w, flags=gtk.DIALOG_DESTROY_WITH_PARENT, type=gtk.MESSAGE_WARNING,
                       buttons=gtk.BUTTONS_OK, message_format=message)
        m.run()
        m.destroy()    
    def __exit(self, event):
        self.__timeOut()
    def __time(self, event):
        self.__clock.hide()
    def __help(self, event):
        self.__alert("This isn't very helpful, is it?")
    def __confirm(self, event):
        self.__answers.append(self.__radioGroup.get_active_label())
        self.__qCounter.tick()
        self.__buttonConfirm.set_sensitive(False)
        self.__buttonNext.set_sensitive(True)
        self.__radioGroup.clear()
    def __next(self, event):
        self.__buttonConfirm.set_sensitive(True)
        self.__buttonNext.set_sensitive(False)
if __name__ == '__main__':
    App().run()

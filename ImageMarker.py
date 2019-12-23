import imghdr
import os
import sys
import shutil

from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showerror
from PIL import Image, ImageTk

class FileSeq:
    def __init__(self, dir):
        self._dir = os.path.abspath(dir)
        self._orig = os.listdir(dir)
        self._filenames = self._orig.copy()
        self._marks = set()
        self._index = 0

        self._filenames.sort()

    def only_images(self):
        for name in self._orig:
            filepath = os.path.join(self._dir, name)

            if os.path.isdir(filepath) or os.path.islink(filepath) or imghdr.what(filepath) == None:
                self._filenames.remove(name)
                
    def get_split_lists(self):
        lists = list()
        m = list(self._marks)
        m.sort()
        p = 0
        for i in m:
            lists.append(self._filenames[p:i+1])
            p = i + 1
        lists.append(self._filenames[p:len(self._filenames) + 1])
        return lists
        
    def get_pair(self):
        # TODO: This should throw an exception that makes more sense than IndexError
        #       when there aren't enough files.
        return (self._filenames[self._index], self._filenames[self._index + 1])

    def next(self):
        if self._index < len(self._filenames) - 2:
            self._index += 1
            return True
        return False

    def prev(self):
        if self._index > 0:
            self._index -= 1
            return True
        return False
        
    def mark(self):
        self._marks.add(self._index)
    
    def unmark(self):
        self._marks.remove(self._index)
    
    def is_marked(self):
        if self._index in self._marks:
            return True
        return False

    def how_many_marks(self):
        return len(self._marks)

    def get_dir(self):
        return self._dir

    def rewind(self):
        self._index = 0

    def forward(self):
        self._index = len(self._filenames) - 2
        
class SplitSeq:
    def __init__(self, fileseq):
        self.files = fileseq

    def make_dirs(self):
        for i in range(1, self.files.how_many_marks() + 2):
            newdir = os.path.join(self.files.get_dir(), str(i))
            if not os.path.exists(newdir):
                os.mkdir(newdir)

    def copy_files(self):
        olddir = self.files.get_dir()
        lists = self.files.get_split_lists()
        for i in range(len(lists)):
            newdir = os.path.join(self.files.get_dir(), str(i + 1))
            count = 1  
            for f in lists[i]:
                shutil.copyfile(os.path.join(olddir, f), os.path.join(newdir, f))
                count += 1

class MainWindow:
    def __init__(self, master, directory=None):
        self.title = 'ImageMarker'
        self.mark_count = 1
        self.marked = False
        
        self._mainwin = master
        self._mainwin.title(self.title)
        self._mainwin.geometry('1010x600')
        self._mainwin.resizable(0, 0)

        # Menu Bar
        self._menubar = Menu(self._mainwin)
        self._menu_file = Menu(self._menubar)
        self._menu_file.add_command(label='Open Directory', command=self.open)
        self._menu_file.add_command(label='Split Image Files', command=self.split)
        self._menu_file.add_command(label='Quit', command=self._mainwin.destroy)
        self._menu_about = Menu(self._menubar)
        self._menubar.add_cascade(menu=self._menu_file, label='File')
        self._menubar.add_cascade(menu=self._menu_about, label="About")
        self._mainwin['menu'] = self._menubar

        # Image Frame for showing a pair of images
        self._image_frame = ttk.Frame(self._mainwin, relief="groove", borderwidth=2)
        self._imagelabel1 = Label(self._image_frame)
        self._imagelabel2 = Label(self._image_frame)
        self._imagelabel1.grid(row=0, column=1, sticky=(N))
        self._imagelabel2.grid(row=0, column=2, sticky=(N))

        # Main controls
        self._control_frame = ttk.Frame(self._mainwin, relief="ridge", borderwidth=0, padding=(100, 5, 100, 5))
        self._cmark = Checkbutton(self._control_frame, text="Mark", command=self.cmark)
        self._cmark.grid(row=0, column=1)
        self._lcount = Label(self._control_frame, text=self.mark_count)
        self._lcount.grid(row=1, column=1)

        Button(self._control_frame, text="Previous", command=self.prev, width=10).grid(row=0, column=0, sticky=(W))
        Button(self._control_frame, text="Next", command=self.next, width=10).grid(row=0, column=2, sticky=(E))

        # Pack frames
        self._control_frame.pack()
        self._image_frame.pack_propagate(0)
        self._image_frame.pack(fill=BOTH, expand=1)

        # Keyboard Bindings
        self._mainwin.bind('<Right>', self._kbd_next)
        self._mainwin.bind('<Left>', self._kbd_prev)
        self._mainwin.bind('<Key>', self._kbd_mark)
        self._mainwin.bind('<Up>', self._kbd_forward)
        self._mainwin.bind('<Down>', self._kbd_rewind)
        self._mainwin.bind('<Shift-Right>', self._kbd_next_mark)
        self._mainwin.bind('<Shift-Left>', self._kbd_prev_mark)
                
        if directory is not None:
            self.open(directory)

    def open(self, directory=None):
        if directory is None:
            directory = askdirectory()

        os.chdir(directory)
        self.files = FileSeq(directory)
        self.files.only_images()
        try:
            self._images_to_label(self.files.get_pair())
        except IndexError:
            # TODO: This should be handled better. Instead of showing an error and returning, 
            #       a dialog showing the error to the user should be shown and then an exception 
            #       should be thrown for the caller to handle.
            #self._mainwin.withdraw()
            showerror('ImageMarker: No Images', 'Not enough images in the directory.')
            #self._mainwin.destroy()
      
        self._mainwin.title('{0} [{1}]'.format(self.title, directory))

    def prev(self):    
        self.move(self.files.prev)
        
    def next(self):            
        self.move(self.files.next)

    def next_mark(self):
        self.files.next()
        while self.files.is_marked() == False:
            if self.files.next() == False:
                self.prev_mark()
                return
            
    def prev_mark(self):
        self.files.prev()
        while self.files.is_marked() == False:
            if self.files.prev() == False:
                self.next_mark()
                return

    def _kbd_next_mark(self, event):
        self.move(self.next_mark)

    def _kbd_prev_mark(self, event):
        self.move(self.prev_mark)
        
    def _kbd_forward(self, event):
        self.move(self.files.forward)

    def _kbd_rewind(self, event):
        self.move(self.files.rewind)
        
    def move(self, func):
        func()
        self._images_to_label(self.files.get_pair())
        self._fmark()

    def _fmark(self):
        if self.files.is_marked():
            self.marked = True
            self._cmark.select()
        else:
            self.marked = False
            self._cmark.deselect()

        self._lmark()
        
    def cmark(self):
        if self.marked == 0:
            self.marked = True
            self.files.mark()
        else:
            self.marked = False
            self.files.unmark()

        self._lmark()
        
    def _lmark(self):
        self.mark_count = self.files.how_many_marks() + 1
        self._lcount.config(text=self.mark_count)
        
    def _kbd_next(self, event):
        self.next()

    def _kbd_prev(self, event):
        self.prev()

    def _kbd_mark(self, event):
        if event.char == ' ':
            self._cmark.toggle()
            self.cmark()

    def _scale_image(self, image):
        ilarge = 0 if image.size[0] > image.size[1] else 1
        ismall = 1 if ilarge == 0 else 0

        if image.size[ilarge] <= 500:
            return image

        ratio = image.size[ilarge] / image.size[ismall]
        new_size = [0, 0]
        new_size[ilarge] = 500
        new_size[ismall] = int(500 / ratio)
        return image.resize(new_size, Image.HAMMING)

    def _images_to_label(self, pair):
        image1 = self._scale_image(Image.open(pair[0]))
        image2 = self._scale_image(Image.open(pair[1]))
        self._photo1 = ImageTk.PhotoImage(image1)
        self._photo2 = ImageTk.PhotoImage(image2)

        self._imagelabel1.config(image=self._photo1)
        self._imagelabel2.config(image=self._photo2)

    def split(self):
        s = SplitSeq(self.files)
        s.make_dirs()
        s.copy_files()

def main():
    dir = None
    if len(sys.argv) > 1:
         dir = os.path.abspath(sys.argv[1])
    root = Tk()
    w = MainWindow(root, dir)
    root.mainloop()

if __name__ == '__main__':
    main()

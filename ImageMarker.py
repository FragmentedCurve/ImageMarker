import imghdr
import os
import sys
import shutil

from tkinter import *
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
    def __init__(self, master, directory):
        self._image1 = None
        self._image2 = None
        self._photo1 = None
        self._photo2 = None
        self._imagelabel1 = None
        self._imagelabel2 = None
        self.mark_count = 1
        self.marked = False
        
        self._mainwin = master
        os.chdir(directory)
        self.files = FileSeq(directory)
        self.files.only_images()

        self._imagelabel1 = Label(self._mainwin)
        self._imagelabel2 = Label(self._mainwin)

        try:
            self._images_to_label(self.files.get_pair())
        except IndexError:
            # TODO: This should be handled better. Instead of showing an error and returning, 
            #       a dialog showing the error to the user should be shown and then an exception 
            #       should be thrown for the caller to handle.
            self._mainwin.withdraw()
            showerror('ImageMarker: No Images', 'Not enough images in the directory.')
            self._mainwin.destroy()
            return
        self._imagelabel1.grid(row=1, column=0)
        self._imagelabel2.grid(row=1, column=2)

        
        Button(self._mainwin, text="Previous", command=self.prev).grid(row=2, column=0)
        Button(self._mainwin, text="Next", command=self.next).grid(row=2, column=2)
        Button(self._mainwin, text="Split", command=self.split).grid(row=0, column=0)
        Button(self._mainwin, text="Quit", command=self._mainwin.destroy).grid(row=0, column=2)
        self._cmark = Checkbutton(self._mainwin, text="Mark", command=self.cmark)
        self._cmark.grid(row=2, column=1)

        self._lcount = Label(self._mainwin, text=self.mark_count)
        self._lcount.grid(row=0, column=1)

        # Keyboard Bindings
        self._mainwin.bind('<Right>', self._kbd_next)
        self._mainwin.bind('<Left>', self._kbd_prev)
        self._mainwin.bind('<Key>', self._kbd_mark)
        self._mainwin.bind('<Up>', self._kbd_forward)
        self._mainwin.bind('<Down>', self._kbd_rewind)
        self._mainwin.bind('<Shift-Right>', self._kbd_next_mark)
        self._mainwin.bind('<Shift-Left>', self._kbd_prev_mark)
                
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
        self._image1 = self._scale_image(Image.open(pair[0]))
        self._image2 = self._scale_image(Image.open(pair[1]))
        self._photo1 = ImageTk.PhotoImage(self._image1)
        self._photo2 = ImageTk.PhotoImage(self._image2)

        self._imagelabel1.config(image=self._photo1)
        self._imagelabel2.config(image=self._photo2)

    def split(self):
        s = SplitSeq(self.files)
        s.make_dirs()
        s.copy_files()

def main():
    root = Tk()
    root.title('ImageMaker')
    root.geometry('1024x500')

    if len(sys.argv) > 1:
        # Directory was given on the command line
        dirname = os.path.abspath(sys.argv[1])
    else:
        dirname = askdirectory()
    if len(dirname) > 0:
        root.title('ImageMaker [{0}]'.format(dirname))
        w = MainWindow(root, dirname)
        root.mainloop()

if __name__ == '__main__':
    main()

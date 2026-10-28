"""Optional inventory slots; independent of the desktop's nine-slot hotbar."""
import fcntl,json,os,tempfile
from pathlib import Path
from hotbar_store import Store,valid_item
from inventory_common import ROOT

class Shelf(Store):
    def __init__(self,path=None):
        super().__init__(path or ROOT/'inventory-items.json')

    def load(self):
        try:
            items=json.loads(self.path.read_text())
            if not isinstance(items,list) or len(items)!=27:raise ValueError()
            return [item if valid_item(item) else None for item in items]
        except (OSError,ValueError):return [None]*27

    def write(self,items):
        if len(items)!=27 or any(i is not None and not valid_item(i) for i in items):
            raise ValueError('Invalid inventory items')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,path=tempfile.mkstemp(prefix='.inventory-',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w') as f:
                json.dump(items,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
            os.replace(path,self.path)
        finally:
            if os.path.exists(path):os.unlink(path)

    def drop(self,slot,data):
        if type(slot) is not int or not 0<=slot<27:raise ValueError('Choose an inventory slot')
        if isinstance(data,(str,bytes)):
            if len(data)>2048:raise ValueError('Invalid drop')
            data=json.loads(data)
        if not isinstance(data,dict) or not valid_item(data.get('item')):raise ValueError('Drag an installed application')
        with open(str(self.path)+'.lock','w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            items=self.load();source=data.get('inventory_slot');item=data['item']
            if type(source) is int and 0<=source<27 and items[source]==item:
                items[source],items[slot]=items[slot],items[source]
            else:items[slot]=item.copy()
            self.write(items)
        return items

    def clear(self,slot):
        if type(slot) is not int or not 0<=slot<27:raise ValueError('Choose an inventory slot')
        with open(str(self.path)+'.lock','w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            items=self.load();items[slot]=None;self.write(items)

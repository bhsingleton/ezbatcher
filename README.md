# ezbatcher
A DCC agnostic python tool for batch editing scene files.  

## How to use
To open the tool run the following command:  

```
from ezbatcher.ui import qezbatcher

window = qezbatcher.QEzBatcher()
window.show()
```

## Interface
The tool is broken down into 4 segments.  
You're current working directory, the file explorer, the file queue and the tasks queue.  

![image](https://user-images.githubusercontent.com/11181168/219877927-8048f973-ed3d-4f22-a4a7-2278eeee8cce.png)

It's important to note that any scene files processed will automatically be opened and don't require an `OpenSceneTask` instance.  
However, you must create a `SaveSceneTask` instance in order to commit any changes you made in your batch operation.

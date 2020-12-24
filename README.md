# Handling the states of hundreds of objects in groups

In you project you may have hundreds or thousands of objects, they can have states like "todo week2", "accepted", "failed", "ask Thomas", you collect them from other colleagues in PDF, Excel, emails or text memos.

Excel or Calc is very good tool for this task, but searching and editing can be annoying when the amount rises.

So I wrote this program, so that I can copy the names in one list with whatever editor or program, and handle them in groups.

# How to start

```
python3 main.py
```

# Functions

- Project selection

The projects are listed and started with buttons. When a new project is to be created, type the name in text field and press enter.

![image](https://github.com/t-lou/transitions/blob/master/screenshots/projects.png)

- Main

Main panel for one project.

![image](https://github.com/t-lou/transitions/blob/master/screenshots/main.png)

- Input

For adding the list. The input text (above) will be separeted with ***,*** and displayed below for checking.

![image](https://github.com/t-lou/transitions/blob/master/screenshots/input.png)

- Add

Add the input list with given state.

When there is conflict, the operation has no effect, only an error message will be shown.

Force will ignore the conflict and reset the items with given state. ***DO NOT USE UNTIL NECESSARY. This option may cause cocnfusion between tabs due to python-tk problem.***

Split button will seperate the items to a list where the operation has no conflict, and another list where the operation is dangerous. The two lists will be displayed in "Input" part, ready for copying for another input for checking (others-filter). After "split", "execution" should be safe.

![image](https://github.com/t-lou/transitions/blob/master/screenshots/add.png)

- Transit

Transit the input list from source state (text field above) to the target state (text field below).

When there is conflict, the operation has no effect, only an error message will be shown.

Force will ignore the conflict and give the items with target state (non-existing items will still be skipped). ***DO NOT USE UNTIL NECESSARY. This option may cause cocnfusion between tabs due to python-tk problem.***

Split button will seperate the items to a list where the operation has no conflict, and another list where the operation is dangerous. The two lists will be displayed in "Input" part, ready for copying for another input for checking (others-filter). After "split", "execution" should be safe.

![image](https://github.com/t-lou/transitions/blob/master/screenshots/transit.png)

- Remove

Delete the given items (when they are available).

When there is conflict, the operation has no effect, only an error message will be shown.

Force will ignore the conflict and delete all listed items, of course the non-existing items will be skipped. ***DO NOT USE UNTIL NECESSARY. This option may cause cocnfusion between tabs due to python-tk problem.***

Split button will seperate the items to a list where the operation has no conflict, and another list where the operation is dangerous. The two lists will be displayed in "Input" part, ready for copying for another input for checking (others-filter). After "split", "execution" should be safe.

![image](https://github.com/t-lou/transitions/blob/master/screenshots/remove.png)

- Others

Other options like

1. backup: make a backup datebase for the project, logs are not part of backup

2. export: export the states in JSON (with .json extension) or CSV (when the extension is not .json)

3. filter: see below

4. replay: see below 

![image](https://github.com/t-lou/transitions/blob/master/screenshots/others.png)


- Export

Display the states with filtering. The filter consists of item-names (left-above, separated with ",") and item-states (left-below, separated with ","). All filtering conditions are used in one "or" logic. When item-names or item-states is empty, there is no filter on that side.

![image](https://github.com/t-lou/transitions/blob/master/screenshots/filter-all.png)

![image](https://github.com/t-lou/transitions/blob/master/screenshots/filter-result.png)

- Replay

Each operation (add, transit and remove) will generate a log file with the operation name and parameters, with the log files we can rebuild the history of transitions project. The log filename contains the time of action, so that we can select the exact time point.

![image](https://github.com/t-lou/transitions/blob/master/screenshots/replay-input.png)

![image](https://github.com/t-lou/transitions/blob/master/screenshots/replay-output.png)

![image](https://github.com/t-lou/transitions/blob/master/screenshots/replay-result.png)
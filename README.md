# RevDesign

![image](https://user-images.githubusercontent.com/43247197/166245547-8643a918-59a8-425d-91f5-ae0617cc25f6.png)


#### Step 1 - Clone and Install Dependencies:
`git clone https://github.com/connorivy/MapThat.git`

** Optional - create virtual environment `py -3.9 -m venv venv` `venv\Scripts\activate.bat` **

`pip install -r requirements.txt`

#### Step 2 - (Optional) Start Local Speckle Server:
The project backend for RevDesign is my own fork of [Speckle Server](). Instructions on how to deploy the server are [here](https://speckle.guide/dev/server-local-dev.html) Or you could go to [speckle.xyz](speckle.xyz) and upload some data there to work with (this is easier).

#### Step 3 - Send BIM Data To Server:
Send data to the server using my fork of the [Speckle Revit Connector](). The data that needs to be sent are the Revit floor objects, as well as the Shear Wall Plan detail components that are used to mark which walls are shearwall. The Revit family file for the detail component can be found in the zz_helper_files folder.

#### Step 4 - Run the Server Without Multithreading:
`python manage.py runserver --nothreading --noreload`

The mesh generation only works on the main thread

#### Step 5 - Load Stream and Build Shearwalls:
![build shearwalls](https://user-images.githubusercontent.com/43247197/166243244-957fa5f3-0198-494a-9583-ba6d446f3b35.gif)

Enter the stream id of your data in the searchbar at the top. This will load the latest commit from the 'main' branch of your stream. Then click the 'Build Shearwall' button.
This step analyzes the data to look for shear walls that stack and shear walls that connect to each imported diaphragm.

#### Step 6 - Get Mesh:
![speckmesh](https://user-images.githubusercontent.com/43247197/166245308-2d8cab33-8820-4698-851a-4c60c9dcd7e6.gif)

Click the get mesh button and each non-bottom floor diaphram should show a mesh. You can click it to explore the object just like with any other Speckle Object.

#### Step 7 - Analyze Mesh:
![analyzedmesh](https://user-images.githubusercontent.com/43247197/166245093-50166b62-777e-4807-b622-e67581935e38.gif)

Edit the GUI controls in the top right corner. If the 'fixed nodes' option is true, the program will assume the shear walls don't deflect. If it is false, the program will assume each shear wall is spring supported. However, each shearwall still has the same stiffness regardless of length (this assumption is overly conservative). Setting 'fixed nodes' to false will help more of the load to be shared by the longer shear walls which can really help your design.

The 'wind direction' is the direction that the wind is coming from. However, there currently isn't an axis that tells you which way is x any y, so you have to remember which was which in your revit model.

Click the 'Analyze Mesh' button and mess with the GUI controls to view different colorizations of the FEM mesh such as reactions, applied loads, and deflections.

You can also click each shear wall object (they are just Speckle Line Elements) and the last property will the the total shear reaction that you need to design the wall for.




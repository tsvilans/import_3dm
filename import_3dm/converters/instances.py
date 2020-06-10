# MIT License

# Copyright (c) 2018-2019 Nathan Letwory, Joel Putnam, Tom Svilans, Lukas Fertig 

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import bpy
import rhino3dm as r3d
from mathutils import Matrix
from mathutils import Vector
from . import utils


#TODO
#tag collections and references with guids
#test w/ more complex blocks and empty blocks
#proper exception handling

    
def handle_instance_definitions(context, model, toplayer, layername):
    """
    import instance definitions from rhino model as empty collections
    """
  
    if not layername in context.blend_data.collections:
            instance_col = context.blend_data.collections.new(name=layername)
            toplayer.children.link(instance_col)

    for idef in model.InstanceDefinitions:
        idef_col=utils.get_iddata(context.blend_data.collections,idef.Id, idef.Name, None )

        try:
            instance_col.children.link(idef_col)
        except Exception:
            pass

def import_instance_reference(context, ob, iref, name, scale, options):
    #TODO:  insert reduced mesh proxy and hide actual instance in viewport for better performance on large files
    iref.empty_display_size=0.5
    iref.empty_display_type='PLAIN_AXES'
    iref.instance_type='COLLECTION'
    iref.instance_collection = utils.get_iddata(context.blend_data.collections,ob.Geometry.ParentIdefId,"",None)
    xform=list(ob.Geometry.Xform.ToFloatArray(1))
    xform=[xform[0:4],xform[4:8], xform[8:12], xform[12:16]]
    xform[0][3]*=scale 
    xform[1][3]*=scale 
    xform[2][3]*=scale 
    iref.matrix_world = Matrix(xform)
                   

def populate_instance_definitions(context, model, toplayer, layername):
    count = 0
    columns = 8
    grid = 5

    #for every instance definition fish out the instance definition objects and link them to their parent 
    for idef in model.InstanceDefinitions:
        parent=utils.get_iddata(context.blend_data.collections, idef.Id, idef.Name, None)
        objectids=idef.GetObjectIds()

        #calculate position offset to lay out block definitions in xy plane
        offset = Vector((count%columns * grid, (count-count%columns)/columns * grid, 0 ))   
        parent.instance_offset = offset #this sets the offset for the collection instances (read: resets the origin)
        count +=1

        for ob in context.blend_data.objects:
            for uuid in objectids:
                if ob.get('rhid',None) == str(uuid):
                    try:
                        parent.objects.link(ob)
                        ob.location += offset #apply the previously calculated offset to all instance definition objects
                    except Exception:
                        pass


def find_collection(node, layername):
    found = None
    for c in node.children:
        if(c.name == layername):
            found = c
            break
        else:
            found = find_collection(c,layername)
    
    return found
    

def set_instance_viewlayer(context, model, toplayer, layername): 
    #set exclusion state for current view layer
    current_vl = context.view_layer
    current_vl_collection = find_collection(current_vl.layer_collection ,layername)

    try:
        current_vl_collection.exclude = True
    except:
        raise RuntimeWarning("Couldn't set exclusion state for Instance Definitions.")

    
    #get/create instance viewlayer and set exclusion states
    try:    
        instance_vl = context.scene.view_layers[layername]
    except:
        instance_vl = context.scene.view_layers.new(layername) 

    instance_vl_collection = find_collection(instance_vl.layer_collection ,layername)

    for c in instance_vl.active_layer_collection.children:
        c.exclude = True    

    try:
        instance_vl_collection.exclude = False #keep only the instance definitions activated
    except:
        raise RuntimeWarning("Couldn't set exclusion state for Instance Definitions.")
                
    context.window.view_layer = instance_vl #set active view layer
 





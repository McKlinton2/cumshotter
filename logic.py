import bpy
import numpy as np
import math as m
import random
import mathutils

global_cumshot_circle_created=False
global_cumshot_index=1

def create_cumshot(context, selected_object, velocity_curve_mapping):
    obj, curve = make_cumshot_curve(context, context.scene.spline_resolution, selected_object.matrix_world.translation)
    
    velocity=context.scene.velocity
    start_frame=context.scene.start_frame

    # DEBUG
    # for c in velocity_curve_mapping.curves:
    #     for p in c.points:
    #         print(p.location)
    #     print(c.points)
    crv = velocity_curve_mapping.curves[3]
    
    i=0
    for p in curve.splines[0].points:
        
        frame_index=int(start_frame)
        start_frame += context.scene.length
        bpy.context.scene.frame_set(frame_index)
        direction = selected_object.matrix_world.to_quaternion() @ mathutils.Vector((0.0, 0.0, -1.0))
        velocity = context.scene.velocity * velocity_curve_mapping.evaluate(crv, i/context.scene.spline_resolution)
        #print(velocity)
        path = generate_fly_path(selected_object.matrix_world.translation, direction, velocity, context.scene.physics_resolution)

        rand_x = 0
        rand_y = 0
        rand_z = 0
        rand_x = (random.randint(-1000,1000)/1000)*context.scene.randomness
        rand_y = (random.randint(-1000,1000)/1000)*context.scene.randomness
        rand_z = (random.randint(-1000,0)/1000)*context.scene.randomness
        a=0
        for point in path:
            # Ray cast experiments
            # hit, hloc, distance_to_collision = ray_cast_collision(point["pos"], [0,0,1])
            # hit2, hloc2, distance_to_collision2 = ray_cast_collision(point["pos"], [0,0,-1])
            # hit3, hloc3, distance_to_collision3 = ray_cast_collision(point["pos"], point["dir"])
            # if first_run:
            #     print("raycasting",(point["pos"]) , point["dir"])
            #     print(f"Hit distance'{distance_to_collision}")  

            rand_x_scaled = rand_x*(a/len(path))   
            rand_y_scaled = rand_y*(a/len(path)) 
            rand_z_scaled = rand_z*(a/len(path))     
                                                                    
            point["pos"] = [point["pos"][0]+rand_x_scaled, point["pos"][1]+rand_y_scaled, point["pos"][2]+rand_z_scaled]
            # Update point coordinate          
            p.co = (point["pos"] + [1.0]) 
            # Make keyframe for point
            p.keyframe_insert(data_path='co', frame=frame_index, index=-1)
            
            frame_index += 1
            a+=1
        i+=1
        
    bpy.context.scene.frame_set(0)   
    return obj

# Curve for cumshot
def make_cumshot_curve(context, point_count, start_location):

    global global_cumshot_circle_created, global_cumshot_index

    if not "cumshot_circle" in bpy.data.objects.keys():
        # Bevelling object, i.e. circle, for the cumshot thickness
        bpy.ops.curve.primitive_bezier_circle_add(radius=context.scene.thickness, enter_editmode=False, location=start_location)
        global_cumshot_circle_created = True

        for obj in bpy.context.selected_objects:
            obj.name = "cumshot_circle"
            obj.data.name = "cumshot_circle"    
        
    crv = bpy.data.curves.new('crv', 'CURVE')
    crv.dimensions = '3D'

    spline = crv.splines.new(type='NURBS')
    spline.points.add(point_count-1) # theres already one point by default

    # assign the point coordinates to the spline points
    for p in spline.points:
        p.co = ([start_location[0], start_location[1], start_location[2]] + [1.0]) # (add nurbs weight)
    
    # create taper object for side profile
    taper_crv = bpy.data.curves.new('taper_crv', 'CURVE')
    taper_crv.dimensions = '3D'    
    taper_spline = taper_crv.splines.new(type='NURBS')
    taper_spline.points.add(9) # theres already one point by default

    taper_coords=[[0,0],[0,0.5], [0.5,0.4], [4,0.3], [5,0.2], [6,0.2],[7,0.1], [8,0], [9,0], [10,0]]

    for p,co in zip(taper_spline.points,taper_coords):
        p.co = ([co[0], co[1], 0] + [1.0])

    taper_obj = bpy.data.objects.new('cumshot_taper', taper_crv)
    bpy.context.scene.collection.objects.link(taper_obj)
    
    crv.taper_object = taper_obj
    crv.bevel_object = bpy.data.objects["cumshot_circle"]
    crv.use_fill_caps = True 
    crv.bevel_mode = 'OBJECT'
    
    # make a new object with the curve
    obj = bpy.data.objects.new(f'Cumshot_{global_cumshot_index}', crv)
    bpy.context.scene.collection.objects.link(obj)
    global_cumshot_index += 1

    return obj, crv

def generate_fly_path(starting_point, direction, velocity, resolution):
    v = velocity
    g = 9.81
    theta = (m.pi)
    t = np.linspace(0, 5, num=resolution) # Set time as 'continous' parameter.

    path = []
    pos = np.array([starting_point[0], starting_point[1], starting_point[2]])
    dir = np.array([direction[0], direction[1], direction[2]])
    cur = pos
    
    last_pos = pos
    for k in t:
        #print(k)
        d = ((v*k)*np.cos(theta)) # get positions at every point in time
        z = ((v*k)*np.sin(theta))-((0.5*g)*(k**2))

        d_pos = pos+dir*d
        cur = np.array([d_pos[0], d_pos[1], d_pos[2]+z])
        cur_dir = last_pos-cur
        last_pos = cur
        #print(cur)
        path.append({
            "pos": [cur[0],cur[1],cur[2]],      # Current position
            "dir": cur_dir   # Current direction
            })

    return path

def ray_cast_collision(start_pos, direction):
    direction = (direction[0], direction[1], direction[2])
    start_pos = (start_pos[0], start_pos[1], start_pos[2])
    dg = bpy.context.evaluated_depsgraph_get()
    #print("raycast",start_pos,direction)
    cast = bpy.context.scene.ray_cast(dg, start_pos, direction, distance=10)
    distance_to_collision = -1
    #print(cast)
    hit = False
    if cast[0] and not cast[4].name=="curve_object":
        distance_to_collision = (-mathutils.Vector(start_pos)+cast[1]).length
        hit = True
        
    #print(distance_to_collision)
    return hit, cast[1], distance_to_collision

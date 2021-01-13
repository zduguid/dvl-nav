Corrected glider navigation data. From Kolumbo dives in Nov. 2019. 


Time: Data interpolated to constant 8 second frequency (seconds)

x_lmc: local mission coordinates (m)

y_lmc: local mission coordinates (m)

lat: latitude (deg)

lon: longitude (deg)

UTM_N: UTM northings (m)

UTM_E: UTM eastings (m)
*zone 35, letter S

z: depth (m)

vel_over_ground_N,E,D: Velocity over ground given change in x,y,z over time (m/s)

u, v, w: linear body velocities usiv velocities over ground and rotated into body frame (m/s)

roll: (+) banking right (deg)
pitch: (+) tilted upwards (deg)
yaw: (0-360) deg

p, q, r: angular body velocities (rad/s) p --> roll, q--> pitch, r-->yaw

q0, q1, q2, q3: quaternions converted from Euler angles
 

rud_angle: (rad) + starboard

mot_pwr: range (1-9)

batt_pos: (+) fwd in meters

pump_vol: cm^3 hydraulic pump

vel_oc_N, E: ocean current velocities in global frame

vel_oc_u, v: ocean current velocities rotated into body frame
*can be used to approx velocity thru water
*vel_og = vel_oc + vel_tw


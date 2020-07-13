# test_VSP.py
#
# Unit tests for velocity shear propagation algorithm.
#   2020-06-12  zduguid@mit.edu    implemented unit tests


import unittest
import VelocityShearPropagation

class TestOceanCurrentPropagation(unittest.TestCase):
    """Test shear-based ocean current propagation methods."""
    
    def test_bad_ocean_current_format(self):
        with self.assertRaises(ValueError):
            VelocityShearPropagation.OceanCurrent(0,1,None) 
            
    def test_one_observation(self):
        # set up the problem
        z = 0
        t = 0
        water_column = VelocityShearPropagation.WaterColumn(max_depth=20,
            voc_mag_filter=np.inf,voc_delta_mag_filter=np.inf)
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for 
            (u,v,w) in [(1,0,0),(2,0,0),(3,0,0)]]
        voc_ref = VelocityShearPropagation.OceanCurrent(0,0,0)
        water_column.add_shear_node(z,t,shear_list,voc_ref)
        voc0 = water_column.get_voc_at_depth(0)[0]
        voc2 = water_column.get_voc_at_depth(2)[0]
        voc4 = water_column.get_voc_at_depth(4)[0]
        voc6 = water_column.get_voc_at_depth(6)[0]
        
        # test that ShearNodes have the correct flags set
        self.assertTrue(voc0.btm_track)
        self.assertTrue(voc2.fwd_prop)
        self.assertTrue(voc4.fwd_prop)
        self.assertTrue(voc6.fwd_prop)
        
        # test that ocean current velocities are correct
        self.assertEqual(voc0.voc, 
            VelocityShearPropagation.OceanCurrent( 0,0,0))
        self.assertEqual(voc2.voc, 
            VelocityShearPropagation.OceanCurrent(-1,0,0))
        self.assertEqual(voc4.voc, 
            VelocityShearPropagation.OceanCurrent(-2,0,0))
        self.assertEqual(voc6.voc, 
            VelocityShearPropagation.OceanCurrent(-3,0,0))
        
        
    def test_forward_propagation_descending(self):
        # observation 1 
        z = 0
        t = 0
        water_column = VelocityShearPropagation.WaterColumn(max_depth=20,
            voc_mag_filter=np.inf,voc_delta_mag_filter=np.inf)
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for (u,v,w)
            in [(1,0,0),(2,0,0),(3,0,0)]]
        voc_ref = VelocityShearPropagation.OceanCurrent(0,0,0)
        water_column.add_shear_node(z,t,shear_list,voc_ref)
        # observation 2
        z = 2
        t = 1
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for (u,v,w)
            in [(0,0,0),(1,0,0)]]
        voc_ref = VelocityShearPropagation.OceanCurrent()
        water_column.add_shear_node(z,t,shear_list,voc_ref)
        # get shear node lists 
        voc0 = [str(sn.voc) for sn in water_column.get_voc_at_depth(0)]
        voc2 = [str(sn.voc) for sn in water_column.get_voc_at_depth(2)]
        voc4 = [str(sn.voc) for sn in water_column.get_voc_at_depth(4)]
        voc6 = [str(sn.voc) for sn in water_column.get_voc_at_depth(6)]
        # check that lengths correct 
        self.assertEqual(len(voc0), 1)
        self.assertEqual(len(voc2), 1)
        self.assertEqual(len(voc4), 2)
        self.assertEqual(len(voc6), 2)
        # check that correct velocities present 
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(0,0,0)) 
            in voc0)
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(-1,0,0)) 
            in voc2)
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(-1,0,0)) 
            in voc4)
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(-2,0,0)) 
            in voc4)
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(-2,0,0)) 
            in voc6)
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(-3,0,0)) 
            in voc6)
    
    def test_forward_propagation_ascending(self):
        water_column = VelocityShearPropagation.WaterColumn(max_depth=12,
            voc_mag_filter=np.inf,voc_delta_mag_filter=np.inf)
        # observation 1
        z = 8
        t = 0
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for 
            (u,v,w) in [(1,0,0)]]
        direction='ascending'
        voc_ref = VelocityShearPropagation.OceanCurrent(5,0,0)
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # observation 2
        z = 4
        t = 2
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for 
            (u,v,w) in [(-1,0,0),(0,0,0),(1,0,0)]]
        direction='ascending'
        voc_ref = VelocityShearPropagation.OceanCurrent()
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=voc_ref)
        # get shear node lists 
        voc4  = [str(sn.voc) for sn in water_column.get_voc_at_depth(4)]
        voc6  = [str(sn.voc) for sn in water_column.get_voc_at_depth(6)]
        voc8  = [str(sn.voc) for sn in water_column.get_voc_at_depth(8)]
        voc10 = [str(sn.voc) for sn in water_column.get_voc_at_depth(10)]
        # check that lengths correct 
        self.assertEqual(len(voc4),  1)
        self.assertEqual(len(voc6),  1)
        self.assertEqual(len(voc8),  1)
        self.assertEqual(len(voc10), 2)
        # check that correct velocities present 
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(5,0,0)) 
            in voc4)
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(6,0,0)) 
            in voc6)
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(5,0,0)) 
            in voc8)
        self.assertTrue(str(VelocityShearPropagation.OceanCurrent(4,0,0)) 
            in voc10)
        
    def test_back_propagation_descending(self):
        water_column = VelocityShearPropagation.WaterColumn(max_depth=14,
            voc_mag_filter=np.inf,voc_delta_mag_filter=np.inf)
        # observation 1
        z = 2
        t = 1
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) 
            for (u,v,w) in [(.2,.4,-.2),(.2,.4,-.2),(.4,.8,-.4)]]
        direction='descending'
        voc_ref = VelocityShearPropagation.OceanCurrent()
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # observation 2
        z = 6
        t = 2
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) 
            for (u,v,w) in [(.1,.2,-.1),(.2,.4,-.2)]]
        direction='descending'
        voc_ref = VelocityShearPropagation.OceanCurrent()
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # observation 3
        z = 10
        t = 3
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) 
            for (u,v,w) in [(0,0,0)]]
        direction='descending'
        voc_ref = VelocityShearPropagation.OceanCurrent(0,0,0)
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # observation 4
        z = 8
        t = 4
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) 
            for (u,v,w) in [(1,2,-1)]]
        direction='ascending'
        voc_ref = VelocityShearPropagation.OceanCurrent()
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # get shear node lists 
        voc2  = [str(sn.voc) for sn in water_column.get_voc_at_depth(2)]
        voc4  = [str(sn.voc) for sn in water_column.get_voc_at_depth(4)]
        voc6  = [str(sn.voc) for sn in water_column.get_voc_at_depth(6)]
        voc8  = [str(sn.voc) for sn in water_column.get_voc_at_depth(8)]
        voc10 = [str(sn.voc) for sn in water_column.get_voc_at_depth(10)]
        voc12 = [str(sn.voc) for sn in water_column.get_voc_at_depth(12)]
        # check that lengths correct 
        self.assertEqual(len(voc2),  1)
        self.assertEqual(len(voc4),  1)
        self.assertEqual(len(voc6),  1)
        self.assertEqual(len(voc8),  3)
        self.assertEqual(len(voc10), 1)
        self.assertEqual(len(voc12), 1)
        # check that correct velocities present 
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0.4,0.8,-0.4)) in voc2)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0.2,0.4,-0.2)) in voc4)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0.2,0.4,-0.2)) in voc6)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0,0,0))        in voc8)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0.1,0.2,-0.1)) in voc8)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(1,2,-1))       in voc8)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0,0,0))        in voc10)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0,0,0))        in voc12)
        
        
    def test_back_propagation_ascending(self):
        import VelocityShearPropagation
        water_column = VelocityShearPropagation.WaterColumn(max_depth=14,
            voc_mag_filter=np.inf,voc_delta_mag_filter=np.inf)
        # observation 1
        z = 10
        t = 1
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for 
            (u,v,w) in [(2,0,0)]]
        direction='ascending'
        voc_ref = VelocityShearPropagation.OceanCurrent()
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # observation 2
        z = 8
        t = 2
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for 
            (u,v,w) in [(1,0,0)]]
        direction='ascending'
        voc_ref = VelocityShearPropagation.OceanCurrent()
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # observation 3
        z = 2
        t = 3
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for 
            (u,v,w) in [(-1,0,0),(0,0,0),(1,0,0)]]
        direction='ascending'
        voc_ref = VelocityShearPropagation.OceanCurrent(1,0,0)
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # get shear node lists 
        voc2  = [str(sn.voc) for sn in water_column.get_voc_at_depth(2)]
        voc4  = [str(sn.voc) for sn in water_column.get_voc_at_depth(4)]
        voc6  = [str(sn.voc) for sn in water_column.get_voc_at_depth(6)]
        voc8  = [str(sn.voc) for sn in water_column.get_voc_at_depth(8)]
        voc10 = [str(sn.voc) for sn in water_column.get_voc_at_depth(10)]
        voc12 = [str(sn.voc) for sn in water_column.get_voc_at_depth(12)]
        # check that lengths correct 
        self.assertEqual(len(voc2),  1)
        self.assertEqual(len(voc4),  1)
        self.assertEqual(len(voc6),  1)
        self.assertEqual(len(voc8),  1)
        self.assertEqual(len(voc10), 1)
        self.assertEqual(len(voc12), 1)
        # check that correct velocities present 
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(1, 0,0)) in voc2)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(2, 0,0)) in voc4)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(1, 0,0)) in voc6)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0, 0,0)) in voc8)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(-1,0,0)) in voc10)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(-3,0,0)) in voc12)
    
    def test_bin_filter(self):
        water_column = VelocityShearPropagation.WaterColumn(max_depth=14,
            start_filter=2,voc_mag_filter=np.inf,voc_delta_mag_filter=np.inf)
        # observation 1
        z = 0
        t = 1
        shear_list = [VelocityShearPropagation.OceanCurrent(u,v,w) for 
            (u,v,w) in [(1,0,0),(2,0,0),(3,0,0),(4,0,0)]]
        direction='descending'
        voc_ref = VelocityShearPropagation.OceanCurrent(0,0,0)
        water_column.add_shear_node(z,t,shear_list,voc_ref,direction=direction)
        # get shear node lists 
        voc0  = [str(sn.voc) for sn in water_column.get_voc_at_depth(0)]
        voc2  = [str(sn.voc) for sn in water_column.get_voc_at_depth(2)]
        voc4  = [str(sn.voc) for sn in water_column.get_voc_at_depth(4)]
        voc6  = [str(sn.voc) for sn in water_column.get_voc_at_depth(6)]
        voc8  = [str(sn.voc) for sn in water_column.get_voc_at_depth(8)]
        # check that lengths correct 
        self.assertEqual(len(voc0),  1)
        self.assertEqual(len(voc2),  0)
        self.assertEqual(len(voc4),  0)
        self.assertEqual(len(voc6),  1)
        self.assertEqual(len(voc8),  1)
        # check that correct velocities present 
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(0, 0,0)) in voc0)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(-3,0,0)) in voc6)
        self.assertTrue(
            str(VelocityShearPropagation.OceanCurrent(-4,0,0)) in voc8)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored','-v'], exit=False)
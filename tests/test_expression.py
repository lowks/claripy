import claripy
import nose

def test_expression():
    bc = claripy.backend_concrete

    e = claripy.BitVecVal(0x01020304, 32)
    nose.tools.assert_equal(len(e), 32)
    r = e.reversed
    nose.tools.assert_equal(r.resolved_with(bc), 0x04030201)
    nose.tools.assert_equal(len(r), 32)

    nose.tools.assert_equal([ i.model for i in r.chop(8) ], [ 4, 3, 2, 1 ] )

    e1 = r[31:24]
    nose.tools.assert_equal(e1.model, 0x04)
    nose.tools.assert_equal(len(e1), 8)
    nose.tools.assert_equal(e1[2].model, 1)
    nose.tools.assert_equal(e1[1].model, 0)

    ee1 = e1.zero_extend(8)
    nose.tools.assert_equal(ee1.model, 0x0004)
    nose.tools.assert_equal(len(ee1), 16)

    ee1 = claripy.BitVecVal(0xfe, 8).sign_extend(8)
    nose.tools.assert_equal(ee1.model, 0xfffe)
    nose.tools.assert_equal(len(ee1), 16)

    xe1 = [ i.model for i in e1.chop(1) ]
    nose.tools.assert_equal(xe1, [ 0, 0, 0, 0, 0, 1, 0, 0 ])

    a = claripy.BitVecVal(1, 1)
    nose.tools.assert_equal((a+a).model, 2)

    x = claripy.BitVecVal(1, 32)
    nose.tools.assert_equal(x.length, 32)
    y = claripy.LShR(x, 10)
    nose.tools.assert_equal(y.length, 32)

    r = claripy.BitVecVal(0x01020304, 32)
    rr = r.reversed
    rrr = rr.reversed.simplified
    #nose.tools.assert_is(r.model, rrr.model)
    #nose.tools.assert_is(type(rr.model), claripy.A)
    nose.tools.assert_equal(rr.resolved_with(bc), 0x04030201)
    nose.tools.assert_is(r.concat(rr), claripy.Concat(r, rr))

    rsum = r+rr
    nose.tools.assert_equal(rsum.model, 0x05050505)

    r = claripy.BitVec('x', 32)
    rr = r.reversed
    rrr = rr.reversed
    nose.tools.assert_is(r, rrr)

    # test identity
    nose.tools.assert_true(r.identical(rrr))
    nose.tools.assert_false(r.identical(rr))
    ii = claripy.BitVec('ii', 32)
    ij = claripy.BitVec('ij', 32)
    nose.tools.assert_true(ii.identical(ii))
    nose.tools.assert_false(ii.identical(ij))

    si = claripy.SI(bits=32, stride=2, lower_bound=20, upper_bound=100)
    sj = claripy.SI(bits=32, stride=2, lower_bound=10, upper_bound=10)
    sk = claripy.SI(bits=32, stride=2, lower_bound=20, upper_bound=100)
    nose.tools.assert_true(si.identical(si))
    nose.tools.assert_false(si.identical(sj))
    nose.tools.assert_true(si.identical(sk))

    # test hash cache
    nose.tools.assert_is(a+a, a+a)

    # test replacement
    old = claripy.BitVec('old', 32, explicit_name=True)
    new = claripy.BitVec('new', 32, explicit_name=True)
    ooo = claripy.BitVecVal(0, 32)

    old_formula = claripy.If((old + 1)%256 == 0, old+10, old+20)
    print old_formula.dbg_repr()
    new_formula = old_formula.replace(old, new)
    print new_formula.dbg_repr()
    ooo_formula = new_formula.replace(new, ooo)

    print ooo_formula.dbg_repr()

    nose.tools.assert_not_equal(hash(old_formula), hash(new_formula))
    nose.tools.assert_not_equal(hash(old_formula), hash(ooo_formula))
    nose.tools.assert_not_equal(hash(new_formula), hash(ooo_formula))

    nose.tools.assert_equal(old_formula.variables, { 'old' })
    nose.tools.assert_equal(new_formula.variables, { 'new' })
    nose.tools.assert_equal(ooo_formula.variables, ooo.variables)

    nose.tools.assert_true(old_formula.symbolic)
    nose.tools.assert_true(new_formula.symbolic)
    nose.tools.assert_true(new_formula.symbolic)

    nose.tools.assert_equal(str(old_formula).replace('old', 'new'), str(new_formula))
    nose.tools.assert_equal(ooo_formula.model, 20)

    # test AST collapse
    s = claripy.SI(bits=32, stride=0, lower_bound=10, upper_bound=10)
    b = claripy.BVV(20, 32)

    sb = s+b
    nose.tools.assert_is_instance(sb.args[0], claripy.Base)

    bb = b+b
    # this was broken previously -- it was checking if type(bb.args[0]) == A,
    # and it wasn't, but was instead a subclass. leaving this out for now
    # nose.tools.assert_not_is_instance(bb.args[0], claripy.Base)

    # ss = s+s
    # (see above)
    # nose.tools.assert_not_is_instance(ss.args[0], claripy.Base)

    sob = s|b
    # for now, this is collapsed. Presumably, Fish will make it not collapse at some point
    nose.tools.assert_is_instance(sob.args[0], claripy.Base)

    # make sure the AST collapses for delayed ops like reversing
    rb = b.reversed
    #nose.tools.assert_is_instance(rb.args[0], claripy.Base)
    # TODO: Properly delay reversing: should not be eager

    rbi = rb.identical(bb)
    nose.tools.assert_is(rbi, False)

    rbi = rb.identical(rb)
    nose.tools.assert_is(rbi, True)

def test_ite():
    raw_ite(claripy.frontends.FullFrontend)
    raw_ite(claripy.frontends.CompositeFrontend)

def raw_ite(solver_type):
    s = solver_type(claripy.backend_z3)
    x = claripy.BitVec("x", 32)
    y = claripy.BitVec("y", 32)
    z = claripy.BitVec("z", 32)

    ite = claripy.ite_dict(x, {1:11, 2:22, 3:33, 4:44, 5:55, 6:66, 7:77, 8:88, 9:99}, claripy.BitVecVal(0, 32))
    nose.tools.assert_equal(sorted(s.eval(ite, 100)), [ 0, 11, 22, 33, 44, 55, 66, 77, 88, 99 ] )

    ss = s.branch()
    ss.add(ite == 88)
    nose.tools.assert_equal(sorted(ss.eval(ite, 100)), [ 88 ] )
    nose.tools.assert_equal(sorted(ss.eval(x, 100)), [ 8 ] )

    ity = claripy.ite_dict(x, {1:11, 2:22, 3:y, 4:44, 5:55, 6:66, 7:77, 8:88, 9:99}, claripy.BitVecVal(0, 32))
    ss = s.branch()
    ss.add(ity != 11)
    ss.add(ity != 22)
    ss.add(ity != 33)
    ss.add(ity != 44)
    ss.add(ity != 55)
    ss.add(ity != 66)
    ss.add(ity != 77)
    ss.add(ity != 88)
    ss.add(ity != 0)
    ss.add(y == 123)
    nose.tools.assert_equal(sorted(ss.eval(ity, 100)), [ 99, 123 ] )
    nose.tools.assert_equal(sorted(ss.eval(x, 100)), [ 3, 9 ] )
    nose.tools.assert_equal(sorted(ss.eval(y, 100)), [ 123 ] )

    itz = claripy.ite_cases([ (claripy.And(x == 10, y == 20), 33), (claripy.And(x==1, y==2), 3), (claripy.And(x==100, y==200), 333) ], claripy.BitVecVal(0, 32))
    ss = s.branch()
    ss.add(z == itz)
    ss.add(itz != 0)
    nose.tools.assert_equal(ss.eval(y/x, 100), ( 2, ))
    nose.tools.assert_items_equal(sorted([ b.value for b in ss.eval(x, 100) ]), ( 1, 10, 100 ))
    nose.tools.assert_items_equal(sorted([ b.value for b in ss.eval(y, 100) ]), ( 2, 20, 200 ))

def test_bool():
    bc = claripy.backend_concrete

    a = claripy.And(*[False, False, True])
    nose.tools.assert_equal(a.resolved_with(bc), False)
    a = claripy.And(*[True, True, True])
    nose.tools.assert_equal(a.resolved_with(bc), True)

    o = claripy.Or(*[False, False, True])
    nose.tools.assert_equal(o.resolved_with(bc), True)
    o = claripy.Or(*[False, False, False])
    nose.tools.assert_equal(o.resolved_with(bc), False)

if __name__ == '__main__':
    #test_expression()
    #test_bool()
    test_ite()

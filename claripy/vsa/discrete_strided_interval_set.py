import itertools
import functools

from .strided_interval import StridedInterval

MAX_NUMBER_OF_SI = 256 # We don't collapse until there are more than this many SIs

def apply_on_each_si(f):
    @functools.wraps(f)
    def operator(self, o):
        if isinstance(o, DiscreteStridedIntervalSet):
            # We gotta apply the operation on each single object
            new_si_set = set()

            for a in self._si_set:
                for b in o._si_set:
                    new_si_set.add(getattr(a, f.__name__)(b))

            ret = DiscreteStridedIntervalSet(bits=self.bits, si_set=new_si_set)
            return ret.normalize()

        elif isinstance(o, StridedInterval):
            new_si_set = set()
            for si in self._si_set:
                new_si_set.add(getattr(si, f.__name__)(o))

            ret = DiscreteStridedIntervalSet(bits=self.bits, si_set=new_si_set)
            return ret.normalize()

        else:
            raise ClaripyVSAOperationError('Unsupported operand type %s' % (type(o)))

    return operator

def collapse_operand(f):
    @functools.wraps(f)
    def collapser(self, o):
        if isinstance(o, DiscreteStridedIntervalSet):
            return f(self, o.collapse())
        else:
            return f(self, o)

    return collapser

dsis_id_ctr = itertools.count()

class DiscreteStridedIntervalSet(StridedInterval):
    """
    A DiscreteStridedIntervalSet represents one or more discrete StridedInterval instances.
    """
    def __init__(self, name=None, bits=0, si_set=None):
        if name is None:
            name = "DSIS_%d" % (dsis_id_ctr.next())

        StridedInterval.__init__(self, name=name, bits=bits)

         # Initialize the set for strided intervals
        if si_set is not None and len(si_set):
            self._si_set = si_set

        else:
            self._si_set = set()

        # Update lower_bound and upper_bound
        for si in self._si_set:
            self._update_bounds(si)

    #
    # Properties
    #

    def __repr__(self):
        representatives = ", ".join([ i.__repr__() for i in list(self._si_set)[ : 5] ])
        if self.number_of_values > 5:
            representatives += ", ..."

        return "%s<%d>(%d){%s}" % (self._name, self._bits, self.number_of_values, representatives)

    @property
    def cardinality(self):
        """
        This is an over-approximation of the cardinality of this DSIS.
        :return:
        """
        cardinality = 0
        for si in self._si_set:
            cardinality += si.cardinality
        return cardinality

    @property
    def number_of_values(self):
        return len(self._si_set)

    #
    # Special methods
    #

    def should_collapse(self):
        return self.number_of_values > MAX_NUMBER_OF_SI

    def collapse(self):
        """
        Collapse into a StridedInterval instance.
        :return: A new StridedInterval instance
        """

        if self.cardinality:
            r = None
            for si in self._si_set:
                r = r._union(si) if r is not None else si

            return r

        else:
            # This is an empty StridedInterval...
            return StridedInterval.empty(self._bits)

    def normalize(self):
        """
        Return the collapsed object if should_collapse() is True, otherwise return self.
        :return: A DiscreteStridedIntervalSet object
        """
        if self.should_collapse(): return self.collapse()
        elif self.number_of_values == 1: return list(self._si_set)[0]
        else: return self

    def copy(self):
        copied = DiscreteStridedIntervalSet(bits=self._bits, si_set=self._si_set.copy())

        return copied

    #
    # Operations
    #

    # Logical operations

    @collapse_operand
    def __eq__(self, o):
        """
        Operation ==
        :param o: The other operand
        :return: An instance of BoolResult
        """

        return (self.collapse() == o)

    @collapse_operand
    def __ne__(self, o):
        """
        Operation !=
        :param o: The other operand
        :return: An instance of BoolResult
        """

        return (self.collapse() != o)

    @collapse_operand
    def __gt__(self, o):
        """
        Operation >
        :param o: The other operand
        :return: An instance of BoolResult
        """

        return (self.collapse() > o)

    @collapse_operand
    def __le__(self, o):
        """
        Operation <=
        :param o: The other operand
        :return: An instance of BoolResult
        """

        return (self.collapse() <= o)

    @collapse_operand
    def __lt__(self, o):
        """
        Operation <
        :param o: The other operand
        :return: And instance of BoolResult
        """
        return (self.collapse() < o)

    # Bitwise operations

    @apply_on_each_si
    def __and__(self, o):
        """
        Operation &
        :param o: The other operand
        :return: An instance of DiscreteStridedIntervalSet
        """
        pass

    def __rand__(self, o):
        return self.__and__(o)

    @apply_on_each_si
    def __or__(self, o):
        """
        Operation |
        :param o: The other operand
        :return: An instance of DiscreteStridedIntervalSet
        """
        pass

    def __ror__(self, o):
        return self.__or__(o)

    @apply_on_each_si
    def __xor__(self, o):
        """
        Operation ^
        :param o: The other operand
        :return: An instance of DiscreteStridedIntervalSet
        """
        pass

    def __rxor__(self, o):
        return self.__xor__(o)

    def __neg__(self):
        """
        Operation ~
        :return: The negated value
        """
        new_si_set = set()
        for si in self._si_set:
            new_si_set.add(~si)

        r = DiscreteStridedIntervalSet(bits=self._bits, si_set=new_si_set)
        return r.normalize()

    def __invert__(self):
        """
        Operation ~
        :return: The negated value
        """
        return self.__neg__()

    @apply_on_each_si
    def __lshift__(self, o):
        """
        Operation <<
        :param o: The other operand
        :return: An instance of DiscreteStridedIntervalSet
        """
        pass

    @apply_on_each_si
    def __rshift__(self, o):
        """
        Operation >>
        :param o: The other operand
        :return: An instance of DiscreteStridedIntervalSet
        """
        pass

    @apply_on_each_si
    def concat(self, b):
        """
        Operation concat
        :param b: The other operand to concatenate with
        :return: The concatenated value
        """
        pass

    def extract(self, high_bit, low_bit):
        """
        Operation extract
        :param high_bit: The highest bit to begin extraction
        :param low_bit: The lowest bit to end extraction
        :return: Extracted bits
        """
        # TODO: This method can be optimized

        ret = set()
        bits = high_bit - low_bit + 1

        for si in self._si_set:
            ret.add(si.extract(high_bit, low_bit))

        if len(ret) > 1:
            return DiscreteStridedIntervalSet(bits=bits, si_set=ret)

        else:
            return list(ret)[0]

    # Arithmetic operations

    @apply_on_each_si
    def __add__(self, o):
        """
        Operation +
        :param o: The other operand
        :return:
        """
        pass

    def __radd__(self, o):
        return self.__add__(o)

    @apply_on_each_si
    def __sub__(self, o):
        """
        Operation -
        :param o: The other operand
        :return:
        """
        pass

    def __rsub__(self, o):
        return self.__sub__(o)

    # Evaluation

    def eval(self, n):
        ret = set()

        for si in self._si_set:
            ret |= set(si.eval(n))
            if len(ret) >= n:
                break

        return list(ret)[ : n]

    # Set operations

    def union(self, b):
        if isinstance(b, StridedInterval):
            return self._union_with_si(b)

        elif isinstance(b, DiscreteStridedIntervalSet):
            return self._union_with_dsis(b)

        else:
            raise ClaripyVSAOperationError('Unsupported operand type %s for operation union.' % type(b))

    def intersection(self, b):
        if isinstance(b, StridedInterval):
            return self._intersection_with_si(b)

        elif isinstance(b, DiscreteStridedIntervalSet):
            return self._intersection_with_dsis(b)

        else:
            raise ClaripyVSAOperationError('Unsupported operand type %s for operation intersection.' % type(b))

    # Other operations

    @apply_on_each_si
    def sign_extend(self, new_length):
        """
        Operation SignExt
        :param new_length: The length to extend to
        :return: SignExtended value
        """
        pass

    @apply_on_each_si
    def zero_extend(self, new_length):
        """
        Operation ZeroExt
        :param new_length: The length to extend to
        :return: ZeroExtended value
        """
        pass

    @collapse_operand
    @apply_on_each_si
    def widen(self, b):
        """
        Widening operator
        :param b: The other operand
        :return: The widened result
        """
        pass

    #
    # Private methods
    #

    def _union_with_si(self, si):
        """
        Union with another StridedInterval.
        :param si:
        :return:
        """

        dsis = self.copy()
        for si_ in dsis._si_set:
            if BoolResult.is_true(si_ == si):
                return dsis

        dsis._si_set.add(si)
        dsis._update_bounds(si)

        return dsis.normalize()

    def _union_with_dsis(self, dsis):
        """
        Union with another DiscreteStridedIntervalSet
        :param dsis:
        :return:
        """

        copied = self.copy()

        for a in dsis._si_set:
            copied.union(a)

        copied._update_bounds(dsis)

        return copied.normalize()

    def _intersection_with_si(self, si):
        """
        Intersection with another StridedInterval
        :param si: The other operand
        :return:
        """

        new_si_set = set()
        for si_ in self._si_set:
            r = si_.intersection(si)
            if not r.is_empty():
                new_si_set.add(r)

        if len(new_si_set):
            ret = DiscreteStridedIntervalSet(bits=self.bits, si_set=new_si_set)

            if ret.should_collapse(): return ret.collapse()
            else: return ret

        else:
            # There is no intersection between two operands
            return StridedInterval.empty(self.bits)

    def _intersection_with_dsis(self, dsis):
        """
        Intersection with another DiscreteStridedIntervalSet
        :param dsis: The other operand
        :return:
        """

        new_si_set = set()
        for si in dsis._si_set:
            r = self._intersection_with_si(si)

            if isinstance(r, StridedInterval):
                if not r.is_empty():
                    new_si_set.add(r)

            else: # r is a DiscreteStridedIntervalSet
                new_si_set |= r._si_set

        if len(new_si_set):
            ret = DiscreteStridedIntervalSet(bits=self.bits, si_set=new_si_set)

            return ret.normalize()

        else:
            return StridedInterval.empty(self.bits)

    def _update_bounds(self, val):
        if not isinstance(val, StridedInterval):
            raise ClaripyVSAOperationError('Unsupported operand type %s.' % type(val))

        if val._lower_bound is not None:
            if self._lower_bound is None:
                self._lower_bound = val.lower_bound
            elif val.lower_bound < self._lower_bound:
                self._lower_bound = val.lower_bound

        if val._upper_bound is not None:
            if self._upper_bound is None:
                self._upper_bound = val.upper_bound
            elif val.upper_bound > self._upper_bound:
                self._upper_bound = val.upper_bound

from .errors import ClaripyVSAOperationError
from .bool_result import BoolResult

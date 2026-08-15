import random
import sys
import scipy as sp
import numpy as np
from loguru import logger

from scipy.interpolate import PchipInterpolator

from marketsim.agent.agent import Agent
from marketsim.market.market import Market, Price
from marketsim.fourheap.order import Order
from marketsim.private_values.private_values import PrivateValues
from marketsim.fourheap.constants import BUY, SELL
from typing import List
#from fastcubicspline import FCS
from marketsim.utils.id_generator import id_generator


class HBLAgent(Agent):
    def __init__(self, market: Market, q_max: int, shade: List, L: int, pv_var: float,
                 arrival_rate: float, pv = None, agent_id: int =None):
        super().__init__(market=market)
        self.group = "HBL"
        self.agent_id = agent_id if agent_id is not None else id_generator.next()
        self.market = market
        if pv is not None:
            self.pv = pv
        else:
            self.pv = PrivateValues(q_max, float(pv_var))
        self.position = 0
        self.shade = shade
        self.cash = 0
        self.L = L
        self.grace_period = 1 / arrival_rate
        self.lower_bound_mem = 0
        
        # spoofing accuracy mid point
        self.buy_upper_mid_shade = 99/100 # can be tuned based on order pricing distribution
        self.buy_half_shade = 1/2
        self.sell_half_shade = 1/2
        self.sell_upper_mid_shade = 99/100
        self.prices_before_spoofer = []
        self.prices_after_spoofer = []
        self.sell_before_spoofer = []
        self.sell_after_spoofer = []
        self.sell_count = [0,0]
        self.buy_count = [0,0]

        self.q_max = q_max
        self.pv_var = pv_var

    def get_id(self) -> int:
        return self.agent_id

    def estimate_fundamental(self, current_time: int) -> Price:
        #raise # TODO: AK - not used any more as only last trade decides? still used...
        mean, r, T = self.market.get_info()
        #t = self.market.get_time()
        val = self.market.get_fundamental_value(current_time=current_time)
        rho = (1 - r) ** (T - current_time)

        estimate = (1 - rho) * mean + rho * val
        # print(f'It is time {t} with final time {T} and I observed {val} and my estimate is {rho, estimate}')
        return estimate

    def find_worst_order(self, side: int, order_mem :list[Order], orders: List[Order], current_time: int) -> (Price, float):
        """
        Binary search to find the most competitive order in memory with a belief of 0.
        Args:
            side (int): Buy or Sell.
            order_mem (List[Order]): A sorted list of buy or sell orders.
                Both are sorted in ascending value of belief (for buy, ascending prices; for sell, descending prices)

        Returns:
            price: The price of the most competitive order with the a belief of 0.

            Note: we reverse order_mem for sells so that we can reuse code.
        """
        beginning = 0
        end = len(order_mem) - 1
        while beginning < end:
            mid = (beginning + end) // 2
            mid_belief = self.fast_belief_function(order_mem[mid].price, side, orders)
            if mid != len(order_mem) - 1:
                if mid_belief:
                    if not self.fast_belief_function(order_mem[mid + 1].price, side, orders):
                        return order_mem[mid].price, 0
                    if beginning == mid and mid_belief:
                        return order_mem[mid + 1].price, 0
                    beginning = mid
                else:
                    end = mid
            else:
                return order_mem[mid].price, 0
        return order_mem[0].price, self.belief_function(order_mem[0].price, side, orders, current_time=current_time)

    def get_last_trade_time_step(self) -> int:
        """
        Gets memory boundary time step based on L (how many matched orders considered in memory).

        Returns:
            timestep of earliest contributing order (i.e. the boundary timestep for memory).
        """
        # Assumes that matched_orders is ordered by timestep of trades - well, that is risky...
        last_matched_order_ind = len(self.market.matched_orders) - self.L * 2
        earliest_order_time = min(self.market.matched_orders[last_matched_order_ind:],
                             key=lambda matched_order: matched_order.order.time).order.time
        return earliest_order_time

    def fast_belief_function(self, p: Price, side: int, orders: list[Order]) -> bool:
        """
        To check if belief of order with price p is 0. Used for slightly faster queries in find_worst_order()
        Args:
            p (float): price that will be checked.
            side (int): Buy or Sell.
            orders (List[Order]): Orders in memory

        Returns:
            bool: Whether or not belief is 0
        """
        if side == BUY:
            TBL = 0  # Transact bids less or equal
            AL = 0  # Asks less or equal
            for ind, order in enumerate(orders):
                if order.price <= p and order.order_type == SELL:
                    AL += order.quantity
                for matched_order in self.market.matched_orders:
                    if order.order_id == matched_order.order.order_id:
                        if matched_order.order.order_type == BUY and matched_order.price <= p:
                            TBL += order.quantity
                        break
            return AL + TBL == 0
        else:
            TAG = 0  # Transact ask greater or equal
            BG = 0  # Bid greater or equal
            for ind, order in enumerate(orders):
                if order.price >= p and order.order_type == BUY:
                    BG += order.quantity
                for matched_order in self.market.matched_orders:
                    if order.order_id == matched_order.order.order_id:
                        if matched_order.order.order_type == SELL and matched_order.price >= p:
                            TAG += order.quantity
                        break
            return BG + TAG == 0

    def belief_function(self, p: Price, side: int, orders: list[Order], current_time:int) -> float:
        """
        Calculate belief of order with price p of transacting based on memory
        Args:
            p (float): price that will be checked.
            side (int): Buy or Sell.
            orders (List[Order]): Orders in memory

        Returns:
            float: Probability of order with price p transacting
        """
        p = Price(p)
        if side == BUY:
            TBL = 0  # Transact bids less or equal
            AL = 0  # Asks less or equal
            RBG = 0  # Rejected bids greater or equal
            for ind, order in enumerate(orders):
                if order.price - p <= 0 and order.order_type == SELL:
                    AL += order.quantity
                found_matched = False
                for matched_order in self.market.matched_orders:
                    if order.order_id == matched_order.order.order_id:
                        if matched_order.order.order_type == BUY and matched_order.price - p <= 0:
                            TBL += order.quantity
                        found_matched = True
                        break
                if not found_matched:
                    if order.order_type == BUY and order.price - p >= 0:
                        # order time to withdrawal time
                        withdrawn = False
                        latest_order_time = 0
                        for i in range(ind + 1, len(orders)):
                            if orders[i].agent_id == order.agent_id and orders[i].order_id != order.order_id and orders[i].time > order.time:
                                latest_order_time = orders[i].time
                                withdrawn = True
                                break
                        if not withdrawn:
                            #Order not withdrawn
                            alive_time = current_time - order.time
                            if alive_time >= self.grace_period:
                                #Rejected
                                RBG += order.quantity
                            else:
                                #Partial rejection
                                RBG += (alive_time / self.grace_period) * order.quantity
                        else:
                            #Withdrawal
                            time_till_withdrawal = latest_order_time - order.time
                            #Withdrawal
                            if time_till_withdrawal >= self.grace_period:
                                RBG += order.quantity
                            else:
                                RBG += (time_till_withdrawal / self.grace_period) * order.quantity
                                
            if TBL + AL == 0:
                return 0
            else:
                return (TBL + AL) / (TBL + AL + RBG)

        else:
            TAG = 0  # Transact ask greater or equal
            BG = 0  # Bid greater or equal
            RAL = 0  # Reject ask less or equal

            for order in orders:
                if Price(order.price) - p >= 0 and order.order_type == BUY:
                    BG += order.quantity

            for ind, order in enumerate(orders):
                found_matched = False
                for matched_order in self.market.matched_orders:
                    if order.order_id == matched_order.order.order_id:
                        if matched_order.order.order_type == SELL and matched_order.price - p >= 0:
                            TAG += order.quantity
                        found_matched = True
                        break
                if not found_matched:
                    if order.order_type == SELL and order.price - p <= 0:
                        # order time to withdrawal time
                        withdrawn = False
                        latest_order_time = 0
                        for i in range(ind + 1, len(orders)):
                            if orders[i].agent_id == order.agent_id:
                                latest_order_time = orders[i].time
                                withdrawn = True
                                break
                        if not withdrawn:
                            alive_time = current_time - order.time
                            if alive_time >= self.grace_period:
                                RAL += order.quantity
                            else:
                                RAL += (alive_time / self.grace_period) * order.quantity
                        else:
                            time_till_withdrawal = latest_order_time - order.time
                            if time_till_withdrawal >= self.grace_period:
                                RAL += order.quantity
                            else:
                                RAL += (time_till_withdrawal / self.grace_period) * order.quantity
            if TAG + BG == 0:
                return 0
            else:
                # TODO: sometimes the denominator is equal 0
                return (TAG + BG) / (TAG + BG + RAL)
    
    def get_order_list(self, current_time: int) -> (list, list, list):
        """
        Gets list of orders in memory. 
        
        Returns:
            last_L_orders: list of all orders in memory
            buy_orders_memory: filtered of last_L_orders with just BUY orders
            sell_orders_memory: filtered of last_L_orders with just SELL orders
        """
        #raise # AK - this probably is never called? it is! by determine_optimal_price(...)
        self.lower_bound_mem = self.get_last_trade_time_step() # TODO: gives order, should give int(or time tick)?

        buy_orders_memory = []
        sell_orders_memory = []
        last_L_orders = []
        for time in range(self.lower_bound_mem, current_time+1):
            last_L_orders.extend(self.market.event_queue.scheduled_activities[time])
            # TODO: AK - this is anti-causal - checking also orders which yet didn't reach the LOB!
        buy_orders_memory = [order for order in last_L_orders if order.order_type == BUY]
        sell_orders_memory = [order for order in last_L_orders if order.order_type == SELL]
        return last_L_orders, buy_orders_memory, sell_orders_memory

    # @profile
    def determine_optimal_price(self, side: int, current_time: int) -> (Price, Price):
        """
        Determines optimal price for submission.
        Args:
            side (int): Buy or Sell.
        Returns:
            optimal price of submission and expected surplus weighted by probability of order transacting
        
        Useful references: https://www.sci.brooklyn.cuny.edu/~parsons/courses/840-spring-2009/notes/joel.pdf
            http://spider.sci.brooklyn.cuny.edu/~parsons/courses/840-spring-2005/notes/das.pdf 
        """

        last_L_orders, buy_orders_memory, sell_orders_memory = self.get_order_list(current_time=current_time)
        last_L_orders = np.array(last_L_orders)
        estimate = self.estimate_fundamental(current_time=current_time) # TODO: AK - maybe last traded?
        buy_orders_memory = sorted(buy_orders_memory, key = lambda order:order.price)
        sell_orders_memory = sorted(sell_orders_memory, key = lambda order:order.price)
        best_ask = float(self.market.order_book.sell_unmatched.peek())
        best_buy = float(self.market.order_book.buy_unmatched.peek())
        #First is interpolate objects. Second is corresponding bounds
        spline_interp_objects = [[], []]
        if side == BUY: 
            private_value = self.pv.value_for_exchange(self.position, BUY)
            best_buy_belief = self.belief_function(best_buy, BUY, last_L_orders, current_time=current_time)
            best_ask_belief = 1
            def interpolate(bound1: float, bound2: float, bound1Belief: float, bound2Belief: float, epsilon: float = 0.001):
                #cs = FCS(bound1, bound2+epsilon, [bound1Belief, float(bound2Belief)])
                # TODO: check if this produces exactly the same results:
                cs = PchipInterpolator(
                    [bound1, bound2 + epsilon],
                    [bound1Belief, float(bound2Belief)],
                )

                spline_interp_objects[0].append(cs)
                spline_interp_objects[1].append((bound1, bound2))

            def expected_surplus_max():
                """
                Calculates price with maximum expected surplus.

                Returns:
                    Optimal price and corresponding expected surplus.
                """
                def optimize(price): 
                    """
                    Calculates price with maximum expected surplus.
                    
                    Params:
                        price: Price 

                    Returns:
                        Returns expected surplus of price p.
                    """
                    for i in range(len(spline_interp_objects[0])):
                        # Spline interpolation objects is an array of interpolations over the entire domain. 
                        # There's a different interpolation function for each continuous partition of the domain. 
                        # (I.e. function is piecewise continuous)
                        if spline_interp_objects[1][i][0] <= price <= spline_interp_objects[1][i][1]:
                            return -((estimate + private_value - price) * spline_interp_objects[0][i](price))

                    raise ValueError(f"Price {price} outside spline domain {spline_interp_objects[1]}")

                lb = min(spline_interp_objects[1], key=lambda bound_pair: bound_pair[0])[0]
                ub = max(spline_interp_objects[1], key=lambda bound_pair: bound_pair[1])[1]

                # Because function (when graphed) is well defined to be unimodal, we select 
                # many test points and then local optimize based on best point. 
                # Saves time as opposed to global optimizing.
                test_points = np.linspace(lb, ub, 40)
                vOptimize = np.vectorize(optimize)
                point_surpluses = vOptimize(test_points)
                min_index = np.argmin(point_surpluses)
                min_survey = test_points[min_index]
                
                max_x = sp.optimize.minimize(vOptimize, min_survey, bounds=[[lb, ub]])
                
                return max_x.x.item(), -max_x.fun

            buy_high = float(buy_orders_memory[-1].price)
            buy_high_belief = float(self.belief_function(buy_high, BUY, last_L_orders))
            buy_low, buy_low_belief = self.find_worst_order(BUY, buy_orders_memory, last_L_orders)
            optimal_price = (0,-sys.maxsize)

            if buy_high >= best_ask:
                buy_high = best_ask
                buy_high_belief = best_ask_belief
                buy_low = min(buy_high, buy_low)
                buy_low_belief = min(buy_high_belief, buy_low_belief)
            
            #Best ask > buy high >= best_buy
            if buy_high >= best_buy:
                #interpolate between best ask and buy high
                if best_ask != buy_high:
                    interpolate(buy_high, best_ask, buy_high_belief, 1)
                if best_buy >= buy_low:
                    buy_mid = buy_low + self.buy_upper_mid_shade * abs(best_buy - buy_low)
                    buy_mid_belief = self.belief_function(buy_mid, BUY, last_L_orders)
                    buy_half = buy_low + self.buy_half_shade * abs(best_buy - buy_low)
                    buy_half_belief = self.belief_function(buy_half, BUY, last_L_orders)
                    if best_buy != buy_high:
                        #interpolate between best buy and buy_high 
                        interpolate(best_buy, buy_high, best_buy_belief, buy_high_belief)
                    if best_buy != buy_mid:
                        #interpolate between best buy and buy_mid (for accuracy on spoofing)
                        interpolate(buy_low, buy_half, buy_low_belief, buy_half_belief)
                        interpolate(buy_half, buy_mid, buy_half_belief, buy_mid_belief)
                        interpolate(buy_mid, best_buy, buy_mid_belief, best_buy_belief)
                    if buy_low_belief > 0:
                        #interpolate between buy_low and 0
                        lower_bound = max(buy_low - 2 * (buy_high - buy_low) - 1, 0)
                        interpolate(lower_bound, buy_low, 0, buy_low_belief)
                elif best_buy < buy_low:
                    #interpolate between buy_high and buy_low
                    if buy_high != buy_low:
                        interpolate(buy_low, buy_high, buy_low_belief, buy_high_belief)
                    #interpolate buy_low and best_buy
                    if buy_low != best_buy:
                        interpolate(best_buy, buy_low, best_buy_belief, buy_low_belief)
                    #interpolate best_buy and 0?
                    if best_buy_belief > 0:
                        lower_bound = max(best_buy - 2 * (buy_high - best_buy) - 1,0)
                        buy_mid = lower_bound + self.buy_upper_mid_shade * abs(best_buy - lower_bound)
                        buy_mid_belief = self.belief_function(buy_mid, BUY, last_L_orders)
                        buy_half = lower_bound + self.buy_half_shade * abs(best_buy - lower_bound)
                        buy_half_belief = self.belief_function(buy_half, BUY, last_L_orders)
                        interpolate(buy_mid, best_buy, buy_mid_belief, best_buy_belief)
                        interpolate(buy_half, buy_mid, buy_half_belief, buy_mid_belief)
                        interpolate(lower_bound, buy_half, 0, buy_half_belief)
                        

            elif buy_high < best_buy:
                buy_mid = buy_high + self.buy_upper_mid_shade * abs(best_buy - buy_high)
                buy_mid_belief = self.belief_function(buy_mid, BUY, last_L_orders)
                buy_half = buy_high + self.buy_half_shade * abs(best_buy - buy_high)
                buy_half_belief = self.belief_function(buy_half, BUY, last_L_orders)
                # interpolate between best_ask and best_buy
                if best_ask != best_buy:
                    interpolate(best_buy, best_ask, best_buy_belief, best_ask_belief)
                #interpolate between best_buy and buy_high
                if best_buy != buy_high:
                    interpolate(buy_high, buy_half, buy_high_belief, buy_half_belief)
                    interpolate(buy_half, buy_mid, buy_half_belief, buy_mid_belief)
                    interpolate(buy_mid, best_buy, buy_mid_belief, best_buy_belief)
                    
                #interpolate between buy_high and buy_low
                if buy_high != buy_low:
                    interpolate(buy_low, buy_high, buy_low_belief, buy_high_belief)
                    
                #interpolate buy_low and 0
                if buy_low_belief > 0:
                    #NOTE: Can reconsider this bound for your purposes. If buy high is quite high, this bound distance
                    # could be very far.
                    lower_bound = max(buy_low - 2 * (buy_high - buy_low) - 1, 0)
                    interpolate(lower_bound, buy_low, 0, buy_low_belief)

            optimal_price = expected_surplus_max()
            
            #Assertion check
            if optimal_price == (0,0):
                raise Exception("Optimal price not found in buy calculation.")

            # For edge case: If a lot of orders have expected surplus of 0 (meaning belief of 0),
            # at least submit order that doesn't lose agent money in the edge case
            # that the order submits even if it has belief of 0. 
            if optimal_price[0] > estimate + private_value:
                return estimate + private_value, -1
            
            return optimal_price[0], optimal_price[1]

        else:
            private_value = self.pv.value_for_exchange(self.position, SELL)
            best_buy_belief = 1
            best_ask_belief = self.belief_function(p=Price(best_ask), side=SELL, orders=last_L_orders, current_time=current_time)
            sell_high, sell_high_belief = self.find_worst_order(SELL, sorted(sell_orders_memory, key=lambda order: order.price, reverse=True), last_L_orders, current_time=current_time)
            optimal_price = (0,-sys.maxsize)
            best_buy_belief = 1
            #sell_low = float(sell_orders_memory[0].price) # let's stick to the Price type here, no! scipy needs float!
            sell_low = float(sell_orders_memory[0].price) # probably the price causes "ValueError: x_high must be greater that x_low"
            sell_low_belief = self.belief_function(sell_low, SELL, last_L_orders, current_time=current_time)
            def interpolate(bound1: float, bound2: float, bound1Belief: float, bound2Belief: float, epsilon: float = 0.001) -> None:
                """
                Sell version of interpolate above. 
                @TODO: Merge the two
                """
                logger.debug(
                    "Creating FCS: bound1={}, bound2={}, beliefs=({}, {})",
                    bound1,
                    float(bound2)+epsilon,
                    bound1Belief,
                    bound2Belief,
                )

                assert float(bound2) + epsilon > bound1, f"Invalid interval: {bound1} >= {bound2}"

                #cs = FCS(float(bound1), float(bound2)+epsilon, [float(bound1Belief), float(bound2Belief)])
                # TODO: check if this produces exactly the same results:
                cs = PchipInterpolator(
                    [bound1, bound2 + epsilon],
                    [bound1Belief, float(bound2Belief)],
                )
                spline_interp_objects[0].append(cs)
                spline_interp_objects[1].append((float(bound1), float(bound2)))
                
            def expected_surplus_max():
                """
                Sell version of the same function above in BUY. 
                @TODO: Merge the two
                """
                def optimize(price): 
                    """
                    Sell version of the same function above in BUY. 
                    @TODO: Merge the two
                    """
                    for i in range(len(spline_interp_objects[0])):
                        if spline_interp_objects[1][i][0] <= price <= spline_interp_objects[1][i][1]:
                            return -((price - (estimate + private_value)) * spline_interp_objects[0][i](price))

                    raise ValueError(f"Price {price} outside spline domain {spline_interp_objects[1]}")

                lb = min(spline_interp_objects[1], key=lambda bound_pair: bound_pair[0])[0]
                ub = max(spline_interp_objects[1], key=lambda bound_pair: bound_pair[1])[1]
                test_points = np.linspace(float(lb), float(ub), 40)
                vOptimize = np.vectorize(optimize)
                # AK - fixing for nan values:
                point_surpluses = np.asarray(vOptimize(test_points), dtype=float)

                valid = np.isfinite(point_surpluses)

                if not np.any(valid):
                    raise RuntimeError("Objective function is NaN everywhere.")

                valid_points = test_points[valid]
                valid_surpluses = point_surpluses[valid]

                min_survey = valid_points[np.argmin(valid_surpluses)]

                # point_surpluses = vOptimize(test_points)
                # min_index = np.argmin(point_surpluses)
                # min_survey = test_points[min_index]
                # AK debug
                # print(test_points)
                # print(point_surpluses)
                # print(min_index)
                # print(vOptimize(min_survey)) # it is None
                # print(vOptimize([min_survey]))
                # print(vOptimize(np.array([min_survey])))
                # AK debug end
                max_x = sp.optimize.minimize(vOptimize, min_survey, bounds=[[float(lb), float(ub)]])
                return max_x.x.item(), -max_x.fun

            if best_buy > sell_low:
                sell_low = float(best_buy)
                sell_low_belief = 1
                sell_high = float(max(sell_high, sell_low))
                sell_high_belief = min(sell_high_belief, sell_low_belief)

            if sell_low <= best_ask:
                # interpolate best buy to sell_low
                if sell_low != best_buy:
                    interpolate(best_buy, sell_low, best_buy_belief, sell_low_belief)
                if best_ask <= sell_high:
                    if sell_low != best_ask:
                        sell_mid = float(sell_low) + self.sell_upper_mid_shade * abs(float(best_ask) - float(sell_low))
                        sell_mid_belief = self.belief_function(sell_mid, SELL, last_L_orders, current_time=current_time)
                        sell_half = float(sell_low) + self.sell_half_shade * abs(float(best_ask) - float(sell_low))
                        sell_half_belief = self.belief_function(sell_half, SELL, last_L_orders, current_time=current_time)
                        #interpolate sell_low to sell_mid
                        if sell_low != sell_half:
                            interpolate(sell_low, sell_half, sell_low_belief, sell_half_belief)
                        #interpolate sell_half to sell_mid
                        if sell_half != sell_mid:
                            interpolate(sell_half, sell_mid, sell_half_belief, sell_mid_belief)
                        #interpolate sell_mid to best_ask
                        if sell_mid != best_ask:
                            interpolate(sell_mid, best_ask, sell_mid_belief, best_ask_belief)
                    if best_ask != sell_high:
                        #interpolate best_ask to sell_high
                        interpolate(best_ask, sell_high, best_ask_belief, sell_high_belief)
                        
                    # interpolate sell_high to upper bound, assumed to be high enough to reach prices with probability 0
                    if sell_high_belief > 0:
                        upper_bound = float(sell_high) + 2 * (float(sell_high) - float(best_buy)) + 1
                        interpolate(sell_high, upper_bound, sell_high_belief, 0)
                        
                elif best_ask > sell_high:
                    if sell_low != sell_high:
                        #interpolate low sell to high sell
                        interpolate(sell_low, sell_high, sell_low_belief, sell_high_belief)

                    if sell_high != best_ask:
                        sell_mid = float(sell_high) + self.sell_upper_mid_shade * abs(float(best_ask) - float(sell_high))
                        sell_mid_belief = self.belief_function(sell_mid, SELL, last_L_orders, current_time=current_time)
                        sell_half = float(sell_high) + self.sell_half_shade * abs(float(best_ask) - float(sell_high))
                        sell_half_belief = self.belief_function(sell_half, SELL, last_L_orders, current_time=current_time)
                        #interpolate sell_high to sell_mid
                        if sell_high != sell_half:
                            interpolate(sell_high, sell_half, sell_high_belief, sell_half_belief)
                        if sell_half != sell_mid:
                            interpolate(sell_half, sell_mid, sell_half_belief, sell_mid_belief)
                        #interpolate sell_high to best ask
                        if sell_mid != best_ask:
                            interpolate(sell_mid, best_ask, sell_mid_belief, best_ask_belief)
                        
                    #interpolate sell_high to sell_high + 2*spread
                    if best_ask_belief > 0:
                        upper_bound = best_ask + 2 * (best_ask - best_buy) + 1
                        interpolate(best_ask, upper_bound, best_ask_belief, 0)
                        
            elif sell_low > best_ask:
                if best_buy != best_ask:
                    sell_mid = best_buy + self.sell_upper_mid_shade * abs(best_ask - best_buy)
                    sell_mid_belief = self.belief_function(sell_mid, SELL, last_L_orders, current_time=current_time)
                    sell_half = best_buy + self.sell_half_shade * abs(best_ask - best_buy)
                    sell_half_belief = self.belief_function(sell_half, SELL, last_L_orders, current_time=current_time)
                    #interpolate best_buy to best_ask
                    interpolate(best_buy, sell_half, best_buy_belief, sell_half_belief)
                    interpolate(sell_half, sell_mid, sell_half_belief, sell_mid_belief)
                    #interpolate sell_mid to best_ask
                    interpolate(sell_mid, best_ask, sell_low_belief, best_ask_belief)
                if best_ask != sell_low:
                    #interpolate best_ask to sell_low
                    interpolate(best_ask, sell_low, best_ask_belief, sell_low_belief)
                    
                if sell_low != sell_high:
                    #interpolate sell_low to sell_high
                    interpolate(sell_low, sell_high, sell_low_belief, sell_high_belief)
                    
                #interpolate sell_high to sell_high + 2*spread
                if sell_high_belief > 0:
                    upper_bound = sell_high + 2 * (sell_high - best_buy) + 1
                    interpolate(sell_high, upper_bound, sell_high_belief, 0)
            
            optimal_price = expected_surplus_max()

            if optimal_price == (0,0):
                raise Exception("Error in finding optimal price on sell side.")
            
            #EDGE CASE (SAME AS ABOVE IN BUY)
            if optimal_price[0] < estimate + private_value:
                return estimate + private_value, 0
            
            return optimal_price[0], optimal_price[1]

    def take_action(self, current_time: int, seed: int = 0) -> list[Order]:
        """
        Submits orders to market for HBL.

        Params:
            current_time: current clock tick

        Returns:
            order [Order]: order to be submitted

        Note:
            Behavior reverts to ZI agent if L > total num of trades executed. AK: executed or at least added to LOB?
                or time ticks passed?
        """
        try:
            random.seed(current_time + seed) # AK why not save it somehow to recreate specific scenarios?
            side = random.choice(["BUY", "SELL"])
            #estimate = self.estimate_fundamental(current_time=current_time) # AK: last trade?
            estimate = self.market.last_traded_price
            spread = self.shade[1] - self.shade[0]
            price = estimate
            if len(self.market.matched_orders) >= 2 * self.L and self.market.order_book.buy_unmatched.peek_order() != None and self.market.order_book.sell_unmatched.peek_order() != None:
                # the HBL behavior
                opt_price, opt_price_est_surplus = self.determine_optimal_price(side=side, current_time=current_time)

                order = Order(
                    price=Price(opt_price),
                    quantity=1, #AK well, let's make it bigger to make some profits (Poisson?)
                    agent_id=self.agent_id,
                    time=current_time,
                    order_type=1 if side == 'BUY' else -1,
                    asset_id=self.market.asset_id,
                )
                return [order]

            else:
                # ZI Agent # AK - if there is not enough trades to fill the L memory then behavior the same as ZI
                # AK - but we have changed their behavior already - so let's reuse, and rely on last traded price
                valuation_offset = spread*random.random() + self.shade[0]
                if side == BUY:
                    price = estimate + self.pv.value_for_exchange(self.position, BUY) - valuation_offset
                elif side == SELL:
                    price = estimate + self.pv.value_for_exchange(self.position, SELL) + valuation_offset

                order = Order(
                    price=Price(price),
                    quantity=1,
                    agent_id=self.agent_id,
                    time=current_time,
                    order_type=1 if side == 'BUY' else -1,
                    asset_id=self.market.asset_id,
                )
                return [order]
        except TypeError:
            logger.exception("TypeError in HBLAgent")
            print("TypeError in HBLAgent catched!")

        return []

    def __str__(self) -> str:
        return f'HBL{self.agent_id}'

    def reset(self) -> None:
        self.position = 0
        self.cash = 0
        self.pv = PrivateValues(self.q_max, self.pv_var)

    def get_pos_value(self) -> float:
        return self.pv.value_at_position(self.position)
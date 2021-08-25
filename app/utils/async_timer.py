import asyncio


class Timer:
    def __init__(self, timer_name, interval_secs, callback, context=None, first_immediately=False, expires=False):
        self._interval = interval_secs
        self._first_immediately = first_immediately
        self._name = timer_name
        self._context = context
        self._callback = callback
        self._is_first_call = True
        self._ok = True
        self._task = asyncio.ensure_future(self._job())
        self._callback_count = 0
        self._expires = expires
        self._expired =  False
        print(timer_name + " started")

    @property
    def seconds_awaited(self):
        return self._callback_count*self._interval

    @property
    def name(self):
        return self._name
    
    @property
    def expired(self):
        return self._expired

    async def _job(self):
        try:
            while self._ok:
                if not self._is_first_call or not self._first_immediately:
                    await asyncio.sleep(self._interval)
                self._callback_count += 1
                await self._callback(self._name, self._context, self)
                self._is_first_call = False
                if self._expires:
                    self._expired = True
                    break
        except Exception as ex:
            print(ex)
        self.cancel()

    def cancel(self):
        self._ok = False
        self._task.cancel()
    
    def restart(self):
        self._task.cancel()
        self._ok = True
        self._callback_count = 0
        self._task = asyncio.ensure_future(self._job())


async def some_callback(timer_name, context, timer):
    context['count'] += 1
    print('callback: ' + timer_name + ", count: " + str(context['count']))

    if timer_name == 'Timer 2' and context['count'] == 3:
        timer.cancel()
        if 'tocancel' in context:
            tocancel = context['tocancel']
            print(timer_name+": canceling timer " + tocancel.name)
            tocancel.cancel()
            tocancel.restart()
        print(timer_name + ": goodbye and thanks for all the fish")

async def another_callback(timer_name,context,timer): 
    print(timer_name+": awaited "+str(timer.seconds_awaited)+" seconds")
    if timer.seconds_awaited > 15:
        timer.restart()

if __name__=='__main__':
    timer1 = Timer(interval_secs=1, first_immediately=True, timer_name="Timer 1", context={'count': 0}, callback=some_callback)
    timer3 = Timer("My timer",6,another_callback,context=timer1)
    timer2 = Timer(interval_secs=5,expires=True, first_immediately=False, timer_name="Timer 2", context={'count': 0,'tocancel':timer3}, callback=some_callback)
    try:
        loop = asyncio.get_event_loop()
        loop.run_forever()
    except KeyboardInterrupt:
        timer1.cancel()
        timer2.cancel()
        print("clean up done")

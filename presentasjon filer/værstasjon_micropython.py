from microbit import*
class værstasjon_micropython:
	def __init__(self):A=False;self.num_rain_dumps=0;self.rain_monitor_started=A;self.last_pin_state=1;self.num_wind_turns=0;self.wind_mph=.0;self.wind_monitor_started=A;self.last_wind_pin_state=1;self.last_wind_update_time=0
	def wind_direction(self):
		self.start_wind_monitoring();wind_dir=pin1.read_analog()
		if 886<wind_dir<906:return'0'
		elif 692<wind_dir<712:return'1'
		elif 395<wind_dir<415:return'2'
		elif 478<wind_dir<498:return'3'
		elif 564<wind_dir<584:return'4'
		elif 799<wind_dir<819:return'5'
		elif 968<wind_dir<988:return'6'
		elif 939<wind_dir<959:return'7'
		else:return'8'
	def wind_speed(self):self.start_wind_monitoring();return self.wind_mph
	def check_wind_pulse(self):
		current_state=pin8.read_digital()
		if self.last_wind_pin_state==0 and current_state==1:self.num_wind_turns+=1
		self.last_wind_pin_state=current_state
	def update_wind_speed(self):
		current_time=running_time()
		if current_time-self.last_wind_update_time>=2000:self.wind_mph=self.num_wind_turns/2/1.492;self.num_wind_turns=0;self.last_wind_update_time=current_time
	def start_wind_monitoring(self):
		if self.wind_monitor_started:return
		pin8.set_pull(pin8.PULL_UP);self.last_wind_pin_state=pin8.read_digital();self.last_wind_update_time=running_time();self.wind_monitor_started=True
	def check_rain_pulse(self):
		current_state=pin2.read_digital()
		if self.last_pin_state==0 and current_state==1:self.num_rain_dumps+=1
		self.last_pin_state=current_state
	def start_rain_monitoring(self):
		if self.rain_monitor_started:return
		pin2.set_pull(pin2.PULL_UP);self.last_pin_state=pin2.read_digital();self.rain_monitor_started=True
	def rain_cm(self):self.start_rain_monitoring();inches_of_rain=self.num_rain_dumps*11/1e3;cm_of_rain=inches_of_rain*2.54;return cm_of_rain
	def reset_rain(self):self.num_rain_dumps=0
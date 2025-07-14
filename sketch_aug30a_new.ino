#include <MsTimer2.h> // 引入定时器库，用于周期性地触发中断

#define pwn1In 2  // 定义PWM1输入引脚为数字引脚2
#define pwn2In 3  // 定义PWM2输入引脚为数字引脚3

// 全局变量声明
unsigned long pwm1StartTicks = 0, pwm2StartTicks = 0; // 记录PWM高电平起始时间(微秒)
int pwm1Val = 0, pwm2Val = 0;       // 存储PWM高电平持续时间(us)
int leftOut = 0, rightOut = 0;       // 处理后的输出值
int flag = 0;                         // 状态标志位(0=中立位置,1=有效操作)

// 定时器中断服务函数 (每20ms执行一次)
void onTimer() {

  // 检查PWM值是否在1440-1560us的中立区间，中立区间能够防止设备在应该停止时产生微小抖动
  if (pwm1Val >= 1440 && pwm1Val <= 1560 && pwm2Val >= 1440 && pwm2Val <= 1560) {
    flag = 0;  // 双通道都在中立位置
  } else {
    flag = 1;  // 至少一个通道不在中立位置
  }
    

  if (flag) {

    // 约束PWM值在1000-2000us范围内
    if (pwm1Val > 2000) {
      pwm1Val = 2000;
    } else if (pwm1Val < 1000) {
      pwm1Val = 1000;
    }
    if (pwm2Val > 2000) {
      pwm2Val = 2000;
    } else if (pwm2Val < 1000) {
      pwm2Val = 1000;
    }

    // 将PWM值缩小10倍 (1500us -> 150)
    leftOut = pwm1Val / 10;
    rightOut = pwm2Val / 10;   
  } else {

    // 中立位置时输出0
    leftOut = 0;
    rightOut = 0;
  }
  
  // 通过串口发送数据帧 (固定格式)
  Serial.write(0xA5);      // 帧头标志(起始字节)
  Serial.write(leftOut);  // 左通道输出值
  Serial.write(rightOut); // 右通道输出值
  Serial.write(0x5A);      // 帧尾标志(结束字节)
}

void setup() {
  Serial.begin(115200);    // 初始化串口通信(波特率115200)
  pinMode(6, OUTPUT);      // 设置6号引脚为输出模式
  pinMode(pwn1In, INPUT); // 设置PWM输入引脚为输入模式
  pinMode(pwn2In, INPUT); // 设置PWM输入引脚为输入模式
  
  MsTimer2::set(20, onTimer); // 设置20ms定时中断(触发onTimer)
  MsTimer2::start();         // 启动定时器
  
  // 绑定外部中断处理函数
  attachInterrupt(0, interruptHandle1, CHANGE); // 引脚2(中断0)电平变化触发
  attachInterrupt(1, interruptHandle2, CHANGE); // 引脚3(中断1)电平变化触发
}
 
void loop() {
  // 生成周期20ms的PWM信号(高电平1.5ms)
  digitalWrite(6, HIGH);
  delayMicroseconds(1500);   // 保持高电平1.5ms(默认)
  digitalWrite(6, LOW);
  delayMicroseconds(18500);  // 保持低电平18.5ms（默认）
}
 
// PWM1输入引脚中断处理函数
void interruptHandle1() {
  if (digitalRead(pwn1In) == HIGH) {
    pwm1StartTicks = micros(); // 记录高电平起始时间
  } else {
    pwm1Val = micros() - pwm1StartTicks; // 计算高电平持续时间
  }
}

// PWM2输入引脚中断处理函数
void interruptHandle2() {
  if (digitalRead(pwn2In) == HIGH) {
    pwm2StartTicks = micros(); // 记录高电平起始时间
  } else {
    pwm2Val = micros() - pwm2StartTicks; // 计算高电平持续时间
  }
}
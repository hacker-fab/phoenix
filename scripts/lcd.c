// https://support.newhavendisplay.com/hc/en-us/articles/4414054241175-NHD-C0220BiZ-with-ST7036-I2C-Interface
/*****************************************************/
/*
   C0220BiZ.c
   Program for writing to Newhaven Display Character COG - I2C interface

   (c)2009 Newhaven Display International, Inc. 

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
 */
/*****************************************************/
#include <REG52.H>
/*****************************************************/
code char text1[]={"NEWHAVEN DisplayXXXX"};
code char text2[]={"2x20 LCD Module XXXX"};
/*****************************************************/
sbit SDA = P1^0;						//Serial data
sbit SCL = P3^4;						//Serial clock
                                        //sbit XRESET = HIGH;						//RESET
/*****************************************************/
const char Slave = 0x78;
const char Comsend = 0x00;
const char Datasend = 0x40;
const char Line2 = 0xC0;
/*****************************************************/
void delay(unsigned int n)				//Delay subroutine
{
    unsigned int i,j;
    for (i=0;i<n;i++) {
        for (j=0;j<350;j++) {
            ;
        }
    }
}
/*****************************************************/
void I2C_out(unsigned char j) 			//I2C Output
{
    int n;
    unsigned char d;
    d=j;
    for (n=0;n<8;n++) {
        if ((d&0x80)==0x80) SDA=1;
        else SDA=0;
        d=(d<<1);
        SCL = 0;
        SCL = 1;
        SCL = 0;
    }
    SCL = 1;
    while (SDA==1) {
        SCL=0;
        SCL=1;
    }
    SCL=0;
}
/*****************************************************/
void I2C_Start(void)
{
    SCL=1;
    SDA=1;
    SDA=0;
    SCL=0;
}
/*****************************************************/
void I2C_Stop(void)
{
    SDA=0;
    SCL=0;
    SCL=1;
    SDA=1;
}
/*****************************************************/
void Show(unsigned char *text)
{
    int n,d;
    d=0x00;
    I2C_Start();
    I2C_out(Slave);
    I2C_out(Datasend);
    for(n=0;n<20;n++){
        I2C_out(*text);
        ++text;
    }
    I2C_Stop();
}
/*****************************************************/
void nextline(void)
{
    I2C_Start();
    I2C_out(Slave);
    I2C_out(Comsend);
    I2C_out(Line2);
    I2C_Stop();
}
/****************************************************
 *           Initialization For ST7036i              *
 *****************************************************/
void init_LCD() 
{
    I2C_Start();
    I2C_out(Slave);
    I2C_out(Comsend);
    I2C_out(0x38);
    delay(10);
    I2C_out(0x39);
    delay(10);
    I2C_out(0x14);
    I2C_out(0x78);
    I2C_out(0x5E);
    I2C_out(0x6D);
    I2C_out(0x0C);
    I2C_out(0x01);
    I2C_out(0x06);
    delay(10);
    I2C_Stop();
}
/*****************************************************/
/*****************************************************/
int main(void)
{
    int i;
    P1 = 0;
    P3 = 0;
    while (1) {
        init_LCD();
        delay(2);

        Show(text1);
        nextline();
        Show(text2);
        delay(2000);

        init_LCD();
        delay(2);

        I2C_out(Slave);
        I2C_out(Datasend);
        for (i=0;i<20;i++) {//show first 20 chars in font table
            I2C_out(i);
        }
        I2C_Stop();
        delay(4000);
    }
}


% FOR HELICOPTER NR 3-10
% This file contains the initialization for the helicopter assignment in
% the course TTK4115. Run this file before you execute QuaRC_ -> Build 
% to build the file heli_q8.mdl.

% Oppdatert høsten 2006 av Jostein Bakkeheim
% Oppdatert høsten 2008 av Arnfinn Aas Eielsen
% Oppdatert høsten 2009 av Jonathan Ronen
% Updated fall 2010, Dominik Breu
% Updated fall 2013, Mark Haring
% Updated spring 2015, Mark Haring


%%%%%%%%%%% Calibration of the encoder and the hardware for the specific
%%%%%%%%%%% helicopter
Joystick_gain_x = 1;
Joystick_gain_y = -1;


%%%%%%%%%%% Physical constants
g = 9.81; % gravitational constant [m/s^2]
l_c = 0.46; % distance elevation axis to counterweight [m]
l_h = 0.66; % distance elevation axis to helicopter head [m]
l_p = 0.175; % distance pitch axis to motor [m]
m_c = 1.92; % Counterweight mass [kg]
m_p = 0.72; % Motor mass [kg]
v_s0 = 7.05;
k_f = 0.142;
% p1 = -4;
% p2 = -4;
% p1 = -4 +0.5i;
% p2 = -4 -0.5i;
p1 = -4 +1i;
p2 = -4 -1i;
k_pp = (2*m_p*l_p*p1*p2)/k_f;
k_pd = (-2*m_p*l_p*(p1+p2))/k_f;
% Passe på at runId = siste run sin Id
%runId = 206;

K1 = k_f/(2*m_p*l_p);
K2 = (k_f*l_h)/(m_c*l_c^2 + 2*m_p*l_h^2);
K3 = (k_f*l_h*v_s0)/(m_c*l_c^2 + 2*m_p*(l_h^2 + l_p^2));


A = [0 1 0 0 0; 0 0 0 0 0; 0 0 0 0 0; -1 0 0 0 0; 0 0 -1 0 0];
B = [0 0; 0 K1; K2 0; 0 0; 0 0];
G = [0 0; 0 0; 0 0; 1 0; 0 1];

%A = [0 1 0; 0 0 0; 0 0 0];
%B = [0 0; 0 K1; K2 0];

q11 = 3.6;
q22 = 1;
q33 = 3.6;
q44 = 0.1;
q55 = 10;

r11 = 0.04;
r22 = 0.01;


%Q = [q11 0 0; 0 q22 0; 0 0 q33];
%R = [r11 0; 0 r22];
Q = diag([q11 q22 q33 q44 q55]);
R = diag([r11 r22]);
K = lqr(A, B, Q, R);

F = K(:,[1,3]);

A_obs = [0 1 0 0 0;
         0 0 0 0 0;
         0 0 0 1 0;
         0 0 0 0 0;
         K3 0 0 0 0];

B_obs = [0 0;
         0 K1;
         0 0;
         K2 0;
         0 0];
%slette?
%C_obs = [1 0 0 0 0;0 0 0 0 0;0 0 1 0 0;0 0 0 0 0;0 0 0 0 1];

%p, e, l_dot
%C_obs = [1 0 0 0 0;0 0 1 0 0;0 0 0 0 1];

%e, l_dot
%C_obs = [0 0 1 0 0;0 0 0 0 1];

%alle
C_obs = eye(5);

%slette?
identity_5=[1,1,1,1,1]';


rank(obsv(A_obs,C_obs))


poles = [-2 -3 -4 -5 -6];

L = place(A_obs',C_obs', poles)';
A_est= A_obs-L*C_obs;
B_est=[B_obs L];
C_est=eye(5);
%p, e, l_dot
%D_est=zeros(5,5);
%e, l_dt
%D_est=zeros(5,4);
%alle
D_est=zeros(5,7);


eig(A_obs - L*C_obs)

PORT = 10;

% simulacao.m

% 1. Limpa o workspace e carrega o caso de estudo
clc;
clear;
% Script MATLAB: preparar_dados.m

% Carrega o caso de estudo do MatPower.
% A execucao do arquivo .m cria a variavel 'mpc' no workspace.
mpc = pglib_opf_case73_ieee_rts();

% Extrai as matrizes de dados relevantes para uma nova estrutura simples.
dados_simples.bus = mpc.bus;
dados_simples.gen = mpc.gen;
dados_simples.gencost = mpc.gencost;
dados_simples.branch = mpc.branch;
dados_simples.baseMVA = mpc.baseMVA;

% Salva a nova estrutura em um arquivo .mat, pronto para o Python.
save('dados_para_python.mat', '-struct', 'dados_simples');

disp('Dados do caso de estudo preparados e salvos em "dados_para_python.mat"');
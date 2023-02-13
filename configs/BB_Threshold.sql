SET IDENTITY_INSERT BB_Threshold ON
INSERT INTO BB_Threshold
([ID],[Name],[SetValue],[CurrentValue],[classify],[Description],[RealDescription])
VALUES
(82,N'干燥机露点温度控制点温差',20.00,20.00,N'4',N'干燥机露点温度控制点温差',N'干燥机露点温度控制点温差')
,(83,N'干燥机露点温度控制点上限',20.00,20.00,N'4',N'干燥机露点温度控制点上限',N'干燥机露点温度控制点上限')
,(84,N'干燥机露点温度控制点下限',-40.00,-40.00,N'4',N'干燥机露点温度控制点下限',N'干燥机露点温度控制点下限')
,(85,N'干燥机露点月均气温温差阈值',5.00,5.00,N'4',N'干燥机露点月均气温温差阈值',N'干燥机露点月均气温温差阈值')
,(86,N'干燥机露点节能提高阈值',1.00,1.00,N'4',N'干燥机露点节能提高阈值',N'干燥机露点节能提高阈值')
SET IDENTITY_INSERT BB_Threshold OFF
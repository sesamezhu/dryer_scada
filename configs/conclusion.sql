USE [SCADA]
GO

/****** Object:  Table [dbo].[AP_AdsorptionDryer_Conclusion]    Script Date: 2023-01-13 17:18:57 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[AP_AdsorptionDryer_Conclusion](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[DateTime] [datetime2] NULL,
	[DayID] [char](2) NULL,
	[FactoryID] [char](4) NULL,
	[StationID] [char](4) NULL,
	[EquipID] [char](4) NULL,
	[DewPoint] [decimal](12, 2) NULL,
	[ATower_DewLevel] [decimal](12, 2) NULL,
	[ATower_HeatReduce] [decimal](12, 2) NULL,
	[ATower_DewPoint] [decimal](12, 2) NULL,
	[BTower_DewLevel] [decimal](12, 2) NULL,
	[BTower_HeatReduce] [decimal](12, 2) NULL,
	[BTower_DewPoint] [decimal](12, 2) NULL,
	[DewPoint_Control] [decimal](12, 2) NULL,
	[Heater_Control] [decimal](12, 2) NULL,
	[Regeneration_Control] [decimal](12, 2) NULL,
	[Auto_Control] [decimal](12, 2) NULL,
 CONSTRAINT [PK_AP_AdsorptionDryer_Conclusion] PRIMARY KEY CLUSTERED
(
	[Id] ASC
)
)
GO


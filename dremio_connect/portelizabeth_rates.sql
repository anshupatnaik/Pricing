SELECT
  Customer,
  RateSheetName,
  RateSheetStatus,
  PriceType,
  EffectiveStartDate,
  EffectiveEndDate,
  CategoryName,
  ActivityName,
  RateType,
  UoM,
  ContainerLength,
  ContainerType,
  FreightType,
  Direction,
  IMOClass,
  TierName,
  TierStart,
  TierEnd,
  Currency,
  Rate
FROM "APMT-BEATS"."Global"."insights_and_visualizations"."Pricing"."Customer_Rate_Sheets"
WHERE Terminal = 'Port Elizabeth'
ORDER BY ActivityName, ContainerLength, ContainerType, Direction, Customer

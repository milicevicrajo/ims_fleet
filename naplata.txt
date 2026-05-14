view baza
WITH Granica AS (SELECT DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0) AS PocetakGodine, DATEADD(DAY, 119, DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0)) AS Granica304)
    SELECT n.god, n.sif_par, p.naz_par, n.sif_vrs, n.br_naloga, n.dat_naloga, n.stavka, n.vez_dok, n.datum, n.oj, n.dpo, n.kom, n.skr_naz, n.deviza, n.promena, n.stavka_k, n.d_p, n.knt, ISNULL(n.duguje, 0) AS dug, ISNULL(n.potrazuje, 0) AS pot, 
                      n.sif_pos
    FROM     [PUTGEO-SERVER].bazaims.dbo.nalog_z AS n LEFT OUTER JOIN
                      dbo.partneri AS p ON n.sif_par = p.sif_par AND n.grupa = p.grupa CROSS JOIN
                      Granica AS g
    WHERE  (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() <= g.Granica304) AND (n.god = YEAR(GETDATE()) - 1) AND (n.knt LIKE '20400%' OR
                      n.knt LIKE '20500%') OR
                      (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() <= g.Granica304) AND (n.god = YEAR(GETDATE())) AND (n.knt LIKE '20400%' OR
                      n.knt LIKE '20500%') AND (n.sif_vrs <> 'POC') OR
                      (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() > g.Granica304) AND (n.god = YEAR(GETDATE())) AND (n.knt LIKE '20400%' OR
                      n.knt LIKE '20500%')

view dodela bucketa
WITH dupli AS (SELECT CAST(sif_par AS int) AS sif_par, CONVERT(nvarchar(255), vez_dok) COLLATE Latin1_General_CI_AI AS vez_dok, CAST(dpo AS datetime) AS dpo
                              FROM     dbo.v_duplikati), bez_duplih AS
    (SELECT CAST(v.sif_par AS int) AS sif_par, CONVERT(nvarchar(255), v.vez_dok) COLLATE Latin1_General_CI_AI AS vez_dok, MIN(CAST(v.dpo AS datetime)) AS dpo
     FROM      dbo.v_if AS v LEFT OUTER JOIN
                       dupli AS d ON CAST(v.sif_par AS int) = d.sif_par AND CONVERT(nvarchar(255), v.vez_dok) COLLATE Latin1_General_CI_AI = d.vez_dok COLLATE Latin1_General_CI_AI
     WHERE   (d.sif_par IS NULL)
     GROUP BY CAST(v.sif_par AS int), CONVERT(nvarchar(255), v.vez_dok) COLLATE Latin1_General_CI_AI), bb AS
    (SELECT sif_par, vez_dok COLLATE Latin1_General_CI_AI AS Expr1, dpo
     FROM      dupli
     UNION ALL
     SELECT sif_par, vez_dok COLLATE Latin1_General_CI_AI AS Expr1, dpo
     FROM     bez_duplih)
    SELECT b.sif_par, b.naz_par, b.vez_dok, b.sif_pos, SUM(b.dug) AS duguje, SUM(b.pot) AS potrazuje, SUM(b.dug) - SUM(b.pot) AS saldo, bb.dpo, GETDATE() AS danasnji_datum, DATEDIFF(DAY, bb.dpo, GETDATE()) AS broj_dana, 
                      CASE WHEN DATEDIFF(DAY, bb.dpo, GETDATE()) BETWEEN 1 AND 30 THEN 30 WHEN DATEDIFF(DAY, bb.dpo, GETDATE()) BETWEEN 31 AND 45 THEN 45 WHEN DATEDIFF(DAY, bb.dpo, GETDATE()) BETWEEN 46 AND 
                      60 THEN 60 WHEN DATEDIFF(DAY, bb.dpo, GETDATE()) BETWEEN 61 AND 90 THEN 90 WHEN DATEDIFF(DAY, bb.dpo, GETDATE()) BETWEEN 91 AND 180 THEN 180 WHEN DATEDIFF(DAY, bb.dpo, GETDATE()) 
                      > 180 THEN 181 ELSE 0.1 END AS baket, CASE WHEN DATEDIFF(DAY, bb.dpo, GETDATE()) <= 0 THEN 0 ELSE 1 END AS kategorija, CASE WHEN LEFT(CONVERT(nvarchar(50), knt) COLLATE Latin1_General_CI_AI, 3) 
                      = N'204' THEN 0 ELSE 1 END AS ino
    FROM     dbo.baza AS b LEFT OUTER JOIN
                      bb ON CAST(b.sif_par AS int) = bb.sif_par AND CONVERT(nvarchar(255), b.vez_dok) COLLATE Latin1_General_CI_AI = bb.vez_dok
    GROUP BY b.sif_par, b.naz_par, b.vez_dok, b.sif_pos, LEFT(CONVERT(nvarchar(50), b.knt) COLLATE Latin1_General_CI_AI, 3), bb.dpo
    HAVING (SUM(b.dug) - SUM(b.pot) <> 0)

SELECT sif_pred, grupa, sif_par, naz_par, ulica_par, p_b_par, mesto_par, zr, mb, telefon, fax, email, lice, web, proc_rabata, br_dana, vlasnik, pib, zemlja, proc_rabata1, proc_rabata2, pdv_obveznik, sif_ter, JBKJS, CRF
FROM     [PUTGEO-SERVER].bazaims.dbo.partner
WHERE  (grupa = 1)

view tuzeni
WITH Granica AS (SELECT DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0) AS PocetakGodine, DATEADD(DAY, 119, DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0)) AS Granica304)
    SELECT n.god, n.sif_par, p.naz_par, n.datum, n.knt, k.naz_knt, SUM(ISNULL(n.duguje, 0)) AS duguju, SUM(ISNULL(n.potrazuje, 0)) AS platili
    FROM     [PUTGEO-SERVER].bazaims.dbo.nalog_z AS n LEFT OUTER JOIN
                      dbo.partneri AS p ON n.sif_par = p.sif_par AND n.grupa = p.grupa LEFT OUTER JOIN
                      [PUTGEO-SERVER].bazaims.dbo.konto AS k ON n.knt = k.knt CROSS JOIN
                      Granica AS g
    WHERE  (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() <= g.Granica304) AND (n.god = YEAR(GETDATE()) - 1) AND (n.grupa = 1) AND (n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.promena = 'O') OR
                      (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() <= g.Granica304) AND (n.god = YEAR(GETDATE())) AND (n.grupa = 1) AND (n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.promena = 'O') AND (n.sif_vrs <> 'POC') OR
                      (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() > g.Granica304) AND (n.god = YEAR(GETDATE()) - 1) AND (n.grupa = 1) AND (n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.promena = 'O')
    GROUP BY n.god, n.sif_par, p.naz_par, n.datum, n.knt, k.naz_knt

ispravke
WITH Granica AS (SELECT DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0) AS PocetakGodine, DATEADD(DAY, 119, DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0)) AS Granica304)
    SELECT n.god, n.sif_par, p.naz_par, n.sif_vrs, n.br_naloga, n.dat_naloga, n.stavka, n.vez_dok, n.datum, n.oj, n.dpo, n.kom, n.skr_naz, n.deviza, n.promena, n.stavka_k, n.d_p, n.knt, k.naz_knt, ISNULL(n.duguje, 0) AS dug, ISNULL(n.potrazuje, 0) 
                      AS pot, n.sif_pos
    FROM     [PUTGEO-SERVER].bazaims.dbo.nalog_z AS n LEFT OUTER JOIN
                      dbo.partneri AS p ON n.sif_par = p.sif_par AND n.grupa = p.grupa LEFT OUTER JOIN
                      [PUTGEO-SERVER].bazaims.dbo.konto AS k ON n.knt = k.knt CROSS JOIN
                      Granica AS g
    WHERE  (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() <= g.Granica304) AND (n.god = YEAR(GETDATE()) - 1) AND (n.knt LIKE '2049%' OR
                      n.knt LIKE '2059%' OR
                      n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.grupa = 1) AND (n.sif_pred = 1) OR
                      (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() <= g.Granica304) AND (n.god = YEAR(GETDATE())) AND (n.knt LIKE '2049%' OR
                      n.knt LIKE '2059%' OR
                      n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.grupa = 1) AND (n.sif_pred = 1) AND (n.sif_vrs <> 'POC') OR
                      (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() > g.Granica304) AND (n.god = YEAR(GETDATE()) - 1) AND (n.knt LIKE '2049%' OR
                      n.knt LIKE '2059%' OR
                      n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.grupa = 1) AND (n.sif_pred = 1)

v v_duplikati
WITH Granica AS (SELECT DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0) AS PocetakGodine, DATEADD(DAY, 119, DATEADD(YEAR, DATEDIFF(YEAR, 0, GETDATE()), 0)) AS Granica304)
    SELECT n.god, n.sif_par, p.naz_par, n.sif_vrs, n.br_naloga, n.dat_naloga, n.stavka, n.vez_dok, n.datum, n.oj, n.dpo, n.kom, n.skr_naz, n.deviza, n.promena, n.stavka_k, n.d_p, n.knt, k.naz_knt, ISNULL(n.duguje, 0) AS dug, ISNULL(n.potrazuje, 0) 
                      AS pot, n.sif_pos
    FROM     [PUTGEO-SERVER].bazaims.dbo.nalog_z AS n LEFT OUTER JOIN
                      dbo.partneri AS p ON n.sif_par = p.sif_par AND n.grupa = p.grupa LEFT OUTER JOIN
                      [PUTGEO-SERVER].bazaims.dbo.konto AS k ON n.knt = k.knt CROSS JOIN
                      Granica AS g
    WHERE  (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() <= g.Granica304) AND (n.god = YEAR(GETDATE()) - 1) AND (n.knt LIKE '2049%' OR
                      n.knt LIKE '2059%' OR
                      n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.grupa = 1) AND (n.sif_pred = 1) OR
                      (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() <= g.Granica304) AND (n.god = YEAR(GETDATE())) AND (n.knt LIKE '2049%' OR
                      n.knt LIKE '2059%' OR
                      n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.grupa = 1) AND (n.sif_pred = 1) AND (n.sif_vrs <> 'POC') OR
                      (n.sif_pred = 1) AND (n.god < 2100) AND (n.grupa = 1) AND (GETDATE() > g.Granica304) AND (n.god = YEAR(GETDATE()) - 1) AND (n.knt LIKE '2049%' OR
                      n.knt LIKE '2059%' OR
                      n.knt LIKE '2048%' OR
                      n.knt LIKE '2058%') AND (n.grupa = 1) AND (n.sif_pred = 1)

v_if
SELECT CAST(god AS int) AS god, CAST(MONTH(datum) AS int) AS mesec, CAST(sif_par AS int) AS sif_par, CONVERT(nvarchar(50), oj) COLLATE Latin1_General_CI_AI AS oj, CONVERT(nvarchar(50), sif_pos) COLLATE Latin1_General_CI_AI AS sif_pos,
                   CONVERT(nvarchar(20), sif_vrs) COLLATE Latin1_General_CI_AI AS sif_vrs, TRIM(CONVERT(nvarchar(255), vez_dok)) COLLATE Latin1_General_CI_AI AS vez_dok, CAST(datum AS datetime) AS datum, MIN(CAST(dpo AS datetime)) 
                  AS dpo, SUM(duguje) - SUM(potrazuje) AS saldo
FROM     [putgeo-server].[bazaims].dbo.nalog_z
WHERE  CONVERT(nvarchar(20), sif_vrs) COLLATE Latin1_General_CI_AI = N'IF' AND sif_par > 0 AND god >= 2025
GROUP BY CAST(god AS int), CAST(MONTH(datum) AS int), CAST(sif_par AS int), CONVERT(nvarchar(50), oj) COLLATE Latin1_General_CI_AI, CONVERT(nvarchar(50), sif_pos) COLLATE Latin1_General_CI_AI, CONVERT(nvarchar(20), 
                  sif_vrs) COLLATE Latin1_General_CI_AI, TRIM(CONVERT(nvarchar(255), vez_dok)) COLLATE Latin1_General_CI_AI, CAST(datum AS datetime)
UNION ALL
SELECT CAST(god AS int) AS god, CAST(mesec AS int) AS mesec, CAST(sif_par AS int) AS sif_par, CONVERT(nvarchar(50), oj) COLLATE Latin1_General_CI_AI AS oj, CONVERT(nvarchar(50), sif_pos) COLLATE Latin1_General_CI_AI AS sif_pos, 
                  CONVERT(nvarchar(20), sif_vrs) COLLATE Latin1_General_CI_AI AS sif_vrs, TRIM(CONVERT(nvarchar(255), vez_dok)) COLLATE Latin1_General_CI_AI AS vez_dok, CAST(datum AS datetime) AS datum, CAST(dpo AS datetime) AS dpo, 
                  CAST(saldo AS decimal(18, 2)) AS saldo
FROM     dbo.tabela_IF;
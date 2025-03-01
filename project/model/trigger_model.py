from sqlalchemy import text
from ..app import db

class TriggerManager:

    def __init__(self):
        self.execute_triggers()

    def execute_triggers(self) -> None:
        """
        Execute all trigger methods in the class.

        Trigger methods are methods that start with "trigger_".
        """
        for attr_name in dir(self):
            if attr_name.startswith("trigger_"):
                method = getattr(self, attr_name)
                if callable(method):
                    trigger_str = method()
                    db.session.execute(text(trigger_str))
                    db.session.commit()

    def trigger_limiter_commandes_sur_place_insert(self) -> str:
        """
        On ne peut avoir que 12 commandes sur place en même temps
        """
        return """
        CREATE TRIGGER limiter_commandes_sur_place_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE nb INT;

            SELECT count(*) INTO nb 
            FROM commandes
            WHERE sur_place = 1 and DATE(date) = DATE(NEW.date); 

            IF nb >= 12 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Il y a déjà 12 commandes sur place';
            END IF;
        END;
        """

    def trigger_limiter_commandes_sur_place_update(self) -> str:
        """
        On ne peut avoir que 12 commandes sur place en même temps
        """
        return """
        CREATE TRIGGER limiter_commandes_sur_place_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE nb INT;

            SELECT count(*) INTO nb 
            FROM commandes
            WHERE sur_place = 1 and num_commande != NEW.num_commande and DATE(date) = DATE(NEW.date); 

            IF NEW.sur_place = 1 THEN
                IF nb >= 12 THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Il y a déjà 12 commandes sur place';
                END IF;
            END IF;
        END;
        """

    def trigger_commandes_sur_place_midi_insert(self) -> str:
        """
        Permet de réserver une table uniquement le midi
        """
        return """
        CREATE TRIGGER commandes_sur_place_midi_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            IF NOT (HOUR(NEW.date) = 11 AND MINUTE(NEW.date) >= 30 OR HOUR(NEW.date) BETWEEN 12 AND 13 OR HOUR(NEW.date) = 14 AND MINUTE(NEW.date) = 0) THEN
                IF NEW.sur_place = 1 THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Impossible de commander sur place avant 11h30 et après 14h';
                END IF;
            END IF;
        END;
        """

    def trigger_commandes_sur_place_midi_update(self) -> str:
        """
        Permet de réserver une table uniquement le midi
        """
        return """
        CREATE TRIGGER commandes_sur_place_midi_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            IF NOT (HOUR(NEW.date) = 11 AND MINUTE(NEW.date) >= 30 OR HOUR(NEW.date) BETWEEN 12 AND 13 OR HOUR(NEW.date) = 14 AND MINUTE(NEW.date) = 0) THEN
                IF NEW.sur_place = 1 THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Impossible de commander sur place avant 11h30 et après 14h';
                END IF;
            END IF;
        END;
        """

    def trigger_update_commande(self) -> str:
        """
        Trigger qui empêche de modifier une commande après 15 minutes après la date de la commande
        """
        return """
        CREATE TRIGGER update_commande BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE current DATETIME DEFAULT NOW();

            IF TIMESTAMPDIFF(MINUTE, OLD.date_creation, current) > 15 and OLD.etat != 'Panier' THEN
                IF (NEW.etat != 'Payée' AND NEW.etat != 'Annulée') THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = 'Impossible de modifier une commande après 15 minutes';
                END IF;
            END IF;
        END;
        """

    def trigger_delete_commande(self) -> str:
        """
        Trigger qui empêche de supprimer une commande après 15 minutes après la date de la commande
        """
        return """
        CREATE TRIGGER delete_commande BEFORE DELETE ON commandes FOR EACH ROW
        BEGIN
            DECLARE current DATETIME DEFAULT NOW();


            IF TIMESTAMPDIFF(MINUTE, OLD.date_creation, current) > 15 and OLD.etat != 'Panier' THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de supprimer une commande après 15 minutes';
            END IF;
        END;
        """

    def trigger_reserver_delais_insert(self) -> str:
        """
        Trigger qui empêche de réserver 2 heures avant la date de la commande
        """
        return """
        CREATE TRIGGER reserver_delais_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN

            IF TIMESTAMPDIFF(HOUR, NEW.date_creation, NEW.date) < 2 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Vous ne pouvez pas réserver moins de 2 heures à l'avance";
            END IF;
        END;
        """

    def trigger_reserver_delais_update(self) -> str:
        """
        Trigger qui empêche de réserver 2 heures avant la date de la commande
        """
        return """
        CREATE TRIGGER reserver_delais_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN

            IF TIMESTAMPDIFF(HOUR, NEW.date_creation, NEW.date) < 2 AND NEW.etat != 'Panier' THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de réserver moins de 2 heures avant la date de la commande';
            END IF;
        END;
        """

    #def trigger_commande_non_payee(self) -> str:
    #    """
    #    Trigger qui empêche de commander si l'utilisateur a une commande non payée
    #    """
    #    return """
    #    CREATE TRIGGER commande_non_payee BEFORE INSERT ON commandes FOR EACH ROW
    #    BEGIN
    #        DECLARE nb INT;##

    #        SELECT count(*) INTO nb
    #        FROM commandes
    #        WHERE num_tel = NEW.num_tel AND etat = 'Non payée';

    #        IF nb > 0 THEN
    #            SIGNAL SQLSTATE '45000'
    #            SET MESSAGE_TEXT = 'Vous avez une commande non payée';
    #        END IF;
    #    END;
    #    """

    def trigger_commande_blacklisted_insert(self) -> str:
        """
        Trigger qui empêche de commander si l'utilisateur est blackliste
        """
        return """
        CREATE TRIGGER commande_blacklisted_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            IF (SELECT blackliste FROM user WHERE id_client = NEW.id_client) = 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blackliste';
            END IF;
        END;
        """

    def trigger_commande_blacklisted_update(self) -> str:
        """
        Trigger qui empêche de commander si l'utilisateur est blackliste
        """
        return """
        CREATE TRIGGER commande_blacklisted_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            IF (SELECT blackliste FROM user WHERE id_client = NEW.id_client) = 1 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blackliste';
            END IF;
        END;
        """

    def trigger_black_list_insert(self) -> str:
        """
        Trigger qui ajoute un utilisateur à la blacklist s'il n'est pas 
            venu chercher sa commande
        """
        return """
        CREATE TRIGGER black_list_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE temps INT;
            DECLARE current DATETIME DEFAULT NOW();

            SELECT max((TIMESTAMPDIFF(HOUR, current, date))) INTO temps 
            FROM commandes NATURAL JOIN user
            WHERE id_client = NEW.id_client AND etat = 'Non payée';

            IF temps >= 24 THEN
                UPDATE user
                SET blackliste = True
                WHERE id_client = NEW.id_client;
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blacklisté et ne pouvez plus commander';
            END IF;
        END;
        """

    def trigger_black_list_insert_update(self) -> str:
        """
        Trigger qui ajoute un utilisateur à la blacklist s'il n'est pas 
            venu chercher sa commande
        """
        return """
        CREATE TRIGGER black_list_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE temps INT;
            DECLARE current DATETIME DEFAULT NOW();

            SELECT max((TIMESTAMPDIFF(HOUR, current, date))) INTO temps 
            FROM commandes NATURAL JOIN user
            WHERE id_client = NEW.id_client AND etat = 'Non payée';

            IF temps >= 24 THEN
                UPDATE user
                SET blackliste = True
                WHERE id_client = NEW.id_client;
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Vous êtes blacklisté et ne pouvez plus commander';
            END IF;
        END;
        """

    def trigger_stocks_insert(self) -> str:
        """
        Trigger qui vérifie si il reste assez de plats
            en stock
        """
        return """
        CREATE TRIGGER trigger_stocks_insert BEFORE INSERT ON constituer FOR EACH ROW
        BEGIN
            DECLARE stocks_u INT;
            DECLARE stocks_r INT;

            SELECT stock_utilisable, stock_reserve into stocks_u, stocks_r
            FROM plats
            WHERE id_plat = NEW.id_plat;

            IF stocks_u - NEW.quantite_plat < stocks_r THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Le plat que vous souhaitez n'est plus en stock";
            END IF;
        END;
        """

    def trigger_plats_stocks_update(self) -> str:
        """
        Trigger qui vérifie si il reste assez de plats en stock
        """
        return """
        CREATE TRIGGER trigger_plats_stocks_update BEFORE UPDATE ON plats FOR EACH ROW
        BEGIN
            DECLARE stocks_u INT;
            DECLARE stocks_r INT;

            SELECT stock_utilisable, stock_reserve into stocks_u, stocks_r
            FROM plats
            WHERE id_plat = NEW.id_plat;

            IF NEW.stock_utilisable < NEW.stock_reserve THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Le plat que vous souhaitez n'est plus en stock.";
            END IF;
        END;
        """

    def trigger_stocks_update(self) -> str:
        """
        Trigger qui vérifie si il reste assez de plats
            en stock
        """
        return """
        CREATE TRIGGER trigger_stocks_update BEFORE UPDATE ON constituer FOR EACH ROW
        BEGIN
            DECLARE stocks_u INT;
            DECLARE stocks_r INT;

            SELECT stock_utilisable, stock_reserve into stocks_u, stocks_r
            FROM plats
            WHERE id_plat = NEW.id_plat;

            IF stocks_u - NEW.quantite_plat < stocks_r THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Le plat que vous souhaitez n'est plus en stock";
            END IF;
        END;
        """

    def trigger_table_insert(self) -> str:
        """
        On ne peut réserver une table que si elle est disponible
        """
        return """
        CREATE TRIGGER trigger_table_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE num INT;

            IF (NEW.sur_place = 0 AND NEW.num_table IS NOT NULL) OR (NEW.sur_place = 1 AND NEW.num_table IS NULL) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Il faut remplir 2 champs pour pouvoir réserver une table";
            END IF;

            SELECT num_commande into num
            FROM commandes
            WHERE num_table = NEW.num_table and date = NEW.date;

            IF num IS NOT NULL THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La table est déjà occupée";
            END IF;
        END;
        """

    def trigger_table_update(self) -> str:
        """
        On ne peut réserver une table que si elle est disponible
        """
        return """
        CREATE TRIGGER trigger_table_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            DECLARE num INT;

            IF (NEW.sur_place = 0 AND NEW.num_table IS NOT NULL) OR (NEW.sur_place = 1 AND NEW.num_table IS NULL) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Il faut remplir 2 champs pour pouvoir réserver une table";
            END IF;

            SELECT num_commande into num
            FROM commandes
            WHERE num_table = NEW.num_table and date = NEW.date and num_commande != NEW.num_commande;

            IF num IS NOT NULL THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La table est déjà occupée";
            END IF;
        END;
        """

    def trigger_formule_insert(self) -> str:
        """
        Une formule doit être constituée d'au maximum 4 produits de 
            catégories différentes
        """
        return """
        CREATE TRIGGER trigger_formule_insert BEFORE INSERT ON contenir FOR EACH ROW
        BEGIN
            DECLARE nombre int;
            DECLARE type VARCHAR(62);
            DECLARE n int;

            SELECT count(id_plat) into nombre
            FROM contenir
            WHERE id_formule = NEW.id_formule;

            IF nombre > 3 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La formule est déjà complète";
            END IF;

            SELECT type_plat into type
            FROM plats
            WHERE id_plat = NEW.id_plat;

            SELECT id_plat into n
            FROM contenir
            WHERE id_plat in (
            SELECT id_plat
            FROM plats
            WHERE type_plat = type) and id_formule = NEW.id_formule;

            IF n IS NOT NULL THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La formule contient déjà ce type de plat";
            END IF;
        END;
        """

    def trigger_formule_update(self) -> str:
        """
        Une formule doit être constituée d'au maximum 4 produits de 
            catégories différentes
        """
        return """
        CREATE TRIGGER trigger_formule_update BEFORE UPDATE ON contenir FOR EACH ROW
        BEGIN
            DECLARE cnt INT DEFAULT 0;

            SELECT COUNT(*) INTO cnt
            FROM contenir c
            JOIN plats p ON c.id_plat = p.id_plat
            WHERE c.id_formule = NEW.id_formule
            AND p.type_plat = (SELECT type_plat FROM plats WHERE id_plat = NEW.id_plat)
            AND c.id_plat != OLD.id_plat;

            IF cnt > 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "La formule contient déjà ce type de plat";
            END IF;
        END;
        """

    def trigger_panier_insert(self) -> str:
        """
        Un utilisateur doit avoir un seul et unique panier en même temps
        """
        return """
        CREATE TRIGGER trigger_panier_insert BEFORE insert ON commandes FOR EACH ROW
        BEGIN
            DECLARE id INT;

            IF NEW.etat = "Panier" THEN
                SELECT etat into id FROM commandes
                WHERE id_client = NEW.id_client and
                etat = "Panier";

                IF id IS NOT NULL THEN
                    SIGNAL SQLSTATE '45000'
                    SET MESSAGE_TEXT = "On ne peut avoir qu'un panier à la fois";
                END IF;
            END IF;
        END
        """

    def trigger_ferme_insert(self) -> str:
        """
        Impossible de faire des commandes le lundi ou dimanche
        """
        return """
        CREATE TRIGGER ferme_insert BEFORE INSERT ON commandes FOR EACH ROW
        BEGIN
            IF DAYOFWEEK(NEW.date) IN (1, 2) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de commander le lundi ou le dimanche';
            END IF;
        END;
        """

    def trigger_ferme_update(self) -> str:
        """
        Impossible de faire des commandes le lundi ou dimanche
        """
        return """
        CREATE TRIGGER ferme_update BEFORE UPDATE ON commandes FOR EACH ROW
        BEGIN
            IF DAYOFWEEK(NEW.date) IN (1, 2) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Impossible de commander le lundi ou le dimanche';
            END IF;
        END;
        """

    def trigger_fidelite_insert(self) -> str:
        """
        Permet d'ajouter des points de fidelité à un utilisateur à chaque commande
        """
        return """
        CREATE TRIGGER fidelite_insert AFTER INSERT ON commandes FOR EACH ROW
        BEGIN
            DECLARE user VARCHAR(62);
            DECLARE points INT;

            if NEW.etat = "Payée" THEN
                SELECT id_client into user
                FROM user
                WHERE id_client = NEW.id_client;

                Select points_fidelite into points
                FROM user
                WHERE id_client = user;

                UPDATE user
                SET points_fidelite = points + 10
                WHERE id_client = user;
            END IF;
        END;
        """

    def trigger_reduction_unique_insert(self) -> str:
        """
        Un client ne peut pas avoir plusieurs réductions sur un même plat
        """
        return """
        CREATE TRIGGER reduction_unique_insert BEFORE INSERT ON client_reductions FOR EACH ROW
        BEGIN
            DECLARE plat_id INT;
            DECLARE nb INT;

            SELECT id_plat INTO plat_id
            FROM reduction
            WHERE id_reduction = NEW.id_reduction;
            
            SELECT COUNT(*) INTO nb
            FROM client_reductions cr
            JOIN reduction r ON cr.id_reduction = r.id_reduction
            WHERE cr.id_client = NEW.id_client AND r.id_plat = plat_id;

            IF nb > 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Vous avez déjà une réduction sur ce plat";
            END IF;
        END;
        """

    def trigger_reduction_unique_update(self) -> str:
        """
        Un client ne peut pas avoir plusieurs réductions sur un même plat
        """
        return """
        CREATE TRIGGER reduction_unique_update BEFORE UPDATE ON client_reductions FOR EACH ROW
        BEGIN
            DECLARE plat_id INT;
            DECLARE nb INT;

            SELECT id_plat INTO plat_id
            FROM reduction
            WHERE id_reduction = NEW.id_reduction;
            
            SELECT COUNT(*) INTO nb
            FROM client_reductions cr
            JOIN reduction r ON cr.id_reduction = r.id_reduction
            WHERE cr.id_client = NEW.id_client AND r.id_plat = plat_id;

            IF nb > 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = "Vous avez déjà une réduction sur ce plat";
            END IF;
        END;
        """

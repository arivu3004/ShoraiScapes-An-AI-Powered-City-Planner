import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import io
import base64
from datetime import datetime

class AILayoutPlanner:
    """
    AI-powered city layout planner that generates layouts based on:
    - Population density
    - Temperature
    - Weather conditions
    - Road infrastructure
    - City location
    - Total area
    - City shape
    """
    
    def __init__(self, population, temperature, weather, roads, city="Unknown", total_area=100, shape="rectangular"):
        self.population = population
        self.temperature = temperature
        self.weather = weather
        self.roads = roads
        self.city = city
        self.total_area = total_area  # in square kilometers
        self.shape = shape
        self.grid_size = 1000
        self.layout = np.zeros((self.grid_size, self.grid_size))
        
        # Construction cost multipliers by city/region
        self.city_cost_multipliers = {
            "New York": 1.8,
            "London": 1.7,
            "Tokyo": 1.9,
            "Dubai": 1.6,
            "Singapore": 1.5,
            "Sydney": 1.4,
            "Toronto": 1.3,
            "Mexico City": 0.9,
            "Mumbai": 0.8,
            "Bangkok": 0.9,
            "São Paulo": 0.85,
            "Cairo": 0.7,
            "Default": 1.0
        }
        
    def calculate_density(self):
        """Calculate population density category"""
        if self.population < 10000:
            return "Low"
        elif self.population < 50000:
            return "Medium"
        elif self.population < 200000:
            return "High"
        else:
            return "Very High"
    
    def determine_road_width(self):
        """Determine road width based on population density"""
        density = self.calculate_density()
        
        if density == "Low":
            return 1  # Narrow roads
        elif density == "Medium":
            return 2
        elif density == "High":
            return 3  # Wider roads
        else:
            return 4  # Very wide roads
    
    def suggest_amenities(self):
        """Suggest amenities based on weather and population"""
        amenities = []
        
        # Always include parks
        amenities.append("Parks & Green Spaces")
        
        if int(self.temperature) > 30:
            amenities.extend(["Shopping Malls (indoor)", "Water Fountains", "Cooling Centers"])
        elif int(self.temperature) < 10:
            amenities.extend(["Community Centers", "Recreation Halls"])
        else:
            amenities.extend(["Outdoor Recreation Areas", "Playgrounds"])
        
        # Weather-based suggestions
        if "Rain" in self.weather or "Rainy" in self.weather:
            amenities.append("Underground Drainage System")
            amenities.append("Covered Walkways")
        
        if "Snow" in self.weather:
            amenities.append("Snow Removal Infrastructure")
        
        # Population-based amenities
        density = self.calculate_density()
        if density in ["High", "Very High"]:
            amenities.extend(["Public Transit Hubs", "Hospitals", "Schools", "Markets"])
        
        return list(set(amenities))
    
    def _is_in_city_bounds(self, i, j, shape):
        """Check if a point is within the city bounds based on shape"""
        center = self.grid_size / 2
        margin = 50
        
        if shape.lower() == "circular":
            dist = np.sqrt((i - center) ** 2 + (j - center) ** 2)
            return dist < (center - margin)
        elif shape.lower() == "square":
            return margin < i < (self.grid_size - margin) and margin < j < (self.grid_size - margin)
        elif shape.lower() == "rectangular":
            return margin < i < (self.grid_size - margin) and margin < j < (self.grid_size - margin)
        elif shape.lower() == "triangle":
            vertices = self._triangle_vertices(margin=70)
            return self._point_in_triangle(i, j, vertices)
        elif shape.lower() == "irregular":
            return self._is_in_irregular_bounds(i, j, margin=85)
        return True

    def _triangle_vertices(self, margin=70):
        """Return triangle vertices as (row, col): apex, base-left, base-right."""
        return np.array([
            [margin, self.grid_size // 2],
            [self.grid_size - margin, margin],
            [self.grid_size - margin, self.grid_size - margin],
        ], dtype=float)

    def _point_in_triangle(self, row, col, vertices):
        """Check if a single point is inside triangle using sign method."""
        v1, v2, v3 = vertices

        def sign(r, c, a, b):
            return (c - b[1]) * (a[0] - b[0]) - (a[1] - b[1]) * (r - b[0])

        d1 = sign(row, col, v1, v2)
        d2 = sign(row, col, v2, v3)
        d3 = sign(row, col, v3, v1)
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    def _triangle_city_mask(self, margin=70):
        """Vectorized city mask for triangle shape."""
        vertices = self._triangle_vertices(margin=margin)
        v1, v2, v3 = vertices
        rows, cols = np.indices((self.grid_size, self.grid_size))

        def sign(r, c, a, b):
            return (c - b[1]) * (a[0] - b[0]) - (a[1] - b[1]) * (r - b[0])

        d1 = sign(rows, cols, v1, v2)
        d2 = sign(rows, cols, v2, v3)
        d3 = sign(rows, cols, v3, v1)
        has_neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
        has_pos = (d1 > 0) | (d2 > 0) | (d3 > 0)
        return ~(has_neg & has_pos)

    def _draw_thick_line(self, layout, start, end, width, value):
        """Rasterize a thick line between two (row, col) points."""
        r0, c0 = int(start[0]), int(start[1])
        r1, c1 = int(end[0]), int(end[1])
        steps = int(max(abs(r1 - r0), abs(c1 - c0))) + 1
        rows = np.linspace(r0, r1, steps).astype(int)
        cols = np.linspace(c0, c1, steps).astype(int)
        half = max(1, width // 2)

        for r, c in zip(rows, cols):
            rr0 = max(0, r - half)
            rr1 = min(self.grid_size, r + half + 1)
            cc0 = max(0, c - half)
            cc1 = min(self.grid_size, c + half + 1)
            layout[rr0:rr1, cc0:cc1] = value

    def _circular_city_mask(self, margin=70):
        """Vectorized city mask for circular shape."""
        center = self.grid_size / 2
        rows, cols = np.indices((self.grid_size, self.grid_size))
        dist = np.sqrt((rows - center) ** 2 + (cols - center) ** 2)
        return dist <= (center - margin)

    def _draw_circular_ring(self, layout, center, radius, width, value):
        """Draw a thick circular ring centered at (center, center)."""
        rows, cols = np.indices((self.grid_size, self.grid_size))
        dist = np.sqrt((rows - center) ** 2 + (cols - center) ** 2)
        ring = np.abs(dist - radius) <= (width / 2)
        layout[ring] = value

    def _select_axis_lines(self, counts, target_count, min_gap):
        """Select axis indices from density counts with a minimum spacing."""
        ranked_indices = np.argsort(counts)[::-1]
        selected = []
        for idx in ranked_indices:
            if counts[idx] <= 0:
                break
            if all(abs(idx - s) >= min_gap for s in selected):
                selected.append(int(idx))
            if len(selected) >= target_count:
                break
        return sorted(selected)

    def _refine_roads_with_buildings(self, layout, road_width, road_val, water_val):
        """
        Align roads with realized building distribution:
        - carve main connector roads across dense building bands
        - add local service roads around building edges
        """
        building_mask = np.isin(layout, [2, 3, 5])
        if not np.any(building_mask):
            return

        water_mask = layout == water_val
        half = max(1, road_width // 2)

        # 1) Main connectors derived from dense building rows/columns.
        row_counts = building_mask.sum(axis=1)
        col_counts = building_mask.sum(axis=0)
        target_lines = max(4, self.grid_size // 220)
        min_gap = max(55, road_width * 9)

        row_lines = self._select_axis_lines(row_counts, target_lines, min_gap)
        col_lines = self._select_axis_lines(col_counts, target_lines, min_gap)

        for r in row_lines:
            r0 = max(0, r - half)
            r1 = min(self.grid_size, r + half + 1)
            layout[r0:r1, :] = np.where(water_mask[r0:r1, :], water_val, road_val)

        for c in col_lines:
            c0 = max(0, c - half)
            c1 = min(self.grid_size, c + half + 1)
            layout[:, c0:c1] = np.where(water_mask[:, c0:c1], water_val, road_val)

        # 2) Local access lanes around building edges.
        up = np.zeros_like(building_mask, dtype=bool)
        down = np.zeros_like(building_mask, dtype=bool)
        left = np.zeros_like(building_mask, dtype=bool)
        right = np.zeros_like(building_mask, dtype=bool)
        up[1:, :] = building_mask[:-1, :]
        down[:-1, :] = building_mask[1:, :]
        left[:, 1:] = building_mask[:, :-1]
        right[:, :-1] = building_mask[:, 1:]

        adjacent_to_building = up | down | left | right
        empty_or_park = (layout == 0) | (layout == 4)

        # Thinning pattern to avoid overfilling with roads.
        rows, cols = np.indices(layout.shape)
        thinning = ((rows + cols) % 3 == 0)
        service_roads = adjacent_to_building & empty_or_park & thinning & (~water_mask)
        layout[service_roads] = road_val

        # Keep water untouched.
        layout[water_mask] = water_val

    def _is_in_irregular_bounds(self, i, j, margin=85):
        """Check a single point against an irregular city boundary."""
        center = self.grid_size / 2
        dy = i - center
        dx = j - center
        dist = np.sqrt(dy * dy + dx * dx)
        angle = np.arctan2(dy, dx)

        radius = (
            (center - margin)
            + 55 * np.sin(3 * angle)
            + 35 * np.cos(5 * angle)
            + 18 * np.sin((i + j) / 140)
        )
        return dist < radius

    def _irregular_city_mask(self, margin=85):
        """Vectorized irregular city mask used for clipping and road generation."""
        center = self.grid_size / 2
        rows, cols = np.indices((self.grid_size, self.grid_size))
        dy = rows - center
        dx = cols - center
        dist = np.sqrt(dy * dy + dx * dx)
        angle = np.arctan2(dy, dx)

        radius = (
            (center - margin)
            + 55 * np.sin(3 * angle)
            + 35 * np.cos(5 * angle)
            + 18 * np.sin((rows + cols) / 140)
        )
        return dist < radius
    
    def generate_layout_grid(self):
        """Generate a highly realistic city layout with detailed buildings, roads, and infrastructure"""
        layout = np.zeros((self.grid_size, self.grid_size))
        shape = self.shape.lower()
        
        # Zone type constants
        EMPTY = 0
        ROAD = 1
        RESIDENTIAL = 2
        COMMERCIAL = 3
        PARK = 4
        INDUSTRIAL = 5
        WATER = 6
        
        # Road parameters based on density
        road_spacing = 60 if self.calculate_density() in ["High", "Very High"] else 80
        road_width = 8 if self.calculate_density() in ["High", "Very High"] else 6
        center = self.grid_size / 2
        
        if shape == "circular":
            self._create_circular_layout(layout, road_spacing, road_width, ROAD, center)
        elif shape == "triangle":
            self._create_triangle_layout(layout, road_spacing, road_width, ROAD, center)
        elif shape == "irregular":
            self._create_irregular_layout(layout, road_spacing, road_width, ROAD, center)
        else:  # rectangular/square
            self._create_grid_layout(layout, road_spacing, road_width, ROAD)

        # Add water bodies after roads so water remains visible in the final render
        self._add_water_bodies(layout, WATER, shape, center)
        # Add road borders around water bodies (and keep water interiors road-free)
        self._add_water_border_roads(layout, WATER, ROAD)
        
        # Add detailed buildings within blocks
        self._add_detailed_buildings(layout, road_spacing, road_width, shape, center)
        # Make road network follow the realized building distribution.
        self._refine_roads_with_buildings(layout, road_width, ROAD, WATER)

        # Keep non-rectangular layouts strictly clipped to their bounds.
        if shape == "circular":
            circular_mask = self._circular_city_mask(margin=70)
            layout[~circular_mask] = EMPTY
        elif shape == "triangle":
            tri_mask = self._triangle_city_mask(margin=70)
            layout[~tri_mask] = EMPTY
        elif shape == "irregular":
            irregular_mask = self._irregular_city_mask(margin=85)
            layout[~irregular_mask] = EMPTY
        
        return layout
    
    def _add_water_bodies(self, layout, water_val, shape, center):
        """Add water bodies (lakes/rivers) to the city"""
        if shape == "circular":
            # River-like water strip through the middle for circular plans
            for i in range(self.grid_size):
                for j in range(int(center - 20), int(center + 20)):
                    if layout[i, j] == 0:
                        layout[i, j] = water_val
            return

        if shape in ["square", "rectangular"]:
            # Square water bodies for square/rectangular city plans.
            water_squares = [
                (int(self.grid_size * 0.16), int(self.grid_size * 0.62), 170),
                (int(self.grid_size * 0.70), int(self.grid_size * 0.22), 120),
            ]
            for top, left, size in water_squares:
                bottom = min(self.grid_size, top + size)
                right = min(self.grid_size, left + size)
                square_region = layout[top:bottom, left:right]
                square_region[square_region == 0] = water_val
            return

        # For remaining shapes, use rounded water bodies.
        water_features = [
            (int(self.grid_size * 0.22), int(self.grid_size * 0.72), 90, 130),
            (int(self.grid_size * 0.76), int(self.grid_size * 0.26), 55, 80),
        ]

        for wi, wj, ry, rx in water_features:
            for di in range(-ry, ry + 1):
                for dj in range(-rx, rx + 1):
                    ii = wi + di
                    jj = wj + dj
                    if 0 <= ii < self.grid_size and 0 <= jj < self.grid_size:
                        inside_ellipse = (di * di) / (ry * ry) + (dj * dj) / (rx * rx) <= 1.0
                        if inside_ellipse and layout[ii, jj] == 0:
                            layout[ii, jj] = water_val

    def _add_water_border_roads(self, layout, water_val, road_val):
        """Create a 1-cell road border around water and ensure no road is inside water."""
        water_mask = layout == water_val
        if not np.any(water_mask):
            return

        # Road cannot exist inside water.
        layout[water_mask] = water_val

        # Find all non-water cells touching water (8-neighborhood).
        neighbor_of_water = np.zeros_like(water_mask, dtype=bool)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                shifted = np.zeros_like(water_mask, dtype=bool)

                src_i_start = max(0, -di)
                src_i_end = self.grid_size - max(0, di)
                src_j_start = max(0, -dj)
                src_j_end = self.grid_size - max(0, dj)

                dst_i_start = max(0, di)
                dst_i_end = self.grid_size - max(0, -di)
                dst_j_start = max(0, dj)
                dst_j_end = self.grid_size - max(0, -dj)

                shifted[dst_i_start:dst_i_end, dst_j_start:dst_j_end] = \
                    water_mask[src_i_start:src_i_end, src_j_start:src_j_end]
                neighbor_of_water |= shifted

        border_road_mask = (~water_mask) & neighbor_of_water
        layout[border_road_mask] = road_val
    
    def _create_grid_layout(self, layout, road_spacing, road_width, road_val):
        """Create standard grid layout for rectangular/square cities"""
        for i in range(0, self.grid_size, road_spacing):
            layout[max(0, i-road_width//2):min(self.grid_size, i+road_width//2+1), :] = road_val
        
        for j in range(0, self.grid_size, road_spacing):
            layout[:, max(0, j-road_width//2):min(self.grid_size, j+road_width//2+1)] = road_val
    
    def _create_circular_layout(self, layout, road_spacing, road_width, road_val, center):
        """Create strictly linear roads inside circular boundary."""
        radius_limit = int(center - 70)
        secondary_spacing = max(70, road_spacing)
        primary_width = road_width + 2
        secondary_width = max(2, road_width // 2 + 1)

        # Primary centered axes.
        self._draw_thick_line(layout, (center, 0), (center, self.grid_size - 1), primary_width, road_val)
        self._draw_thick_line(layout, (0, center), (self.grid_size - 1, center), primary_width, road_val)

        # Symmetric parallel horizontal lines.
        offset = secondary_spacing
        while offset < radius_limit:
            self._draw_thick_line(
                layout,
                (center - offset, 0),
                (center - offset, self.grid_size - 1),
                secondary_width,
                road_val,
            )
            self._draw_thick_line(
                layout,
                (center + offset, 0),
                (center + offset, self.grid_size - 1),
                secondary_width,
                road_val,
            )
            offset += secondary_spacing

        # Symmetric parallel vertical lines.
        offset = secondary_spacing
        while offset < radius_limit:
            self._draw_thick_line(
                layout,
                (0, center - offset),
                (self.grid_size - 1, center - offset),
                secondary_width,
                road_val,
            )
            self._draw_thick_line(
                layout,
                (0, center + offset),
                (self.grid_size - 1, center + offset),
                secondary_width,
                road_val,
            )
            offset += secondary_spacing

        # Keep only roads inside the circular city.
        circle_mask = self._circular_city_mask(margin=70)
        layout[~circle_mask] = 0
    
    def _create_triangle_layout(self, layout, road_spacing, road_width, road_val, center):
        """Create clean triangular road hierarchy."""
        vertices = self._triangle_vertices(margin=70)
        v_apex, v_left, v_right = vertices

        # Strong perimeter ring roads along all 3 edges.
        edge_width = road_width + 2
        self._draw_thick_line(layout, v_apex, v_left, edge_width, road_val)
        self._draw_thick_line(layout, v_left, v_right, edge_width, road_val)
        self._draw_thick_line(layout, v_right, v_apex, edge_width, road_val)

        # Primary medians from each vertex to centroid.
        centroid = vertices.mean(axis=0)
        for v in (v_apex, v_left, v_right):
            self._draw_thick_line(layout, v, centroid, road_width + 1, road_val)

        # Secondary roads parallel to each triangle edge (sparser and cleaner).
        for t in np.linspace(0.2, 0.8, 4):
            p1 = (1 - t) * v_apex + t * v_left
            p2 = (1 - t) * v_apex + t * v_right
            self._draw_thick_line(layout, p1, p2, max(2, road_width // 2), road_val)

        for t in (0.35, 0.65):
            p1 = (1 - t) * v_left + t * v_apex
            p2 = (1 - t) * v_left + t * v_right
            self._draw_thick_line(layout, p1, p2, max(2, road_width // 2), road_val)

            p3 = (1 - t) * v_right + t * v_apex
            p4 = (1 - t) * v_right + t * v_left
            self._draw_thick_line(layout, p3, p4, max(2, road_width // 2), road_val)

        # Keep roads strictly within the triangular city boundary.
        tri_mask = self._triangle_city_mask(margin=70)
        layout[~tri_mask] = 0
    
    def _create_irregular_layout(self, layout, road_spacing, road_width, road_val, center):
        """Create clean irregular layout with cross-road pattern."""
        mask = self._irregular_city_mask(margin=85)

        # Primary cross network (broader arterials).
        primary_spacing = max(110, road_spacing + 35)
        primary_width = road_width + 2

        for r in range(110, self.grid_size - 110, primary_spacing):
            r_start = r + int(12 * np.sin(r / 110))
            r_end = r + int(12 * np.cos(r / 130))
            self._draw_thick_line(
                layout,
                (r_start, 70),
                (r_end, self.grid_size - 70),
                primary_width,
                road_val,
            )

        for c in range(110, self.grid_size - 110, primary_spacing):
            c_start = c + int(12 * np.cos(c / 120))
            c_end = c + int(12 * np.sin(c / 100))
            self._draw_thick_line(
                layout,
                (70, c_start),
                (self.grid_size - 70, c_end),
                primary_width,
                road_val,
            )

        # Secondary cross roads (finer grid, slight offsets for organic look).
        secondary_spacing = max(70, road_spacing)
        secondary_width = max(2, road_width // 2 + 1)

        for r in range(95, self.grid_size - 95, secondary_spacing):
            shift = int(8 * np.sin(r / 85))
            self._draw_thick_line(
                layout,
                (r + shift, 85),
                (r + shift, self.grid_size - 85),
                secondary_width,
                road_val,
            )

        for c in range(95, self.grid_size - 95, secondary_spacing):
            shift = int(8 * np.cos(c / 90))
            self._draw_thick_line(
                layout,
                (85, c + shift),
                (self.grid_size - 85, c + shift),
                secondary_width,
                road_val,
            )

        # Clip roads to irregular boundary so edges are clean and precise.
        layout[~mask] = 0
    
    def _add_detailed_buildings(self, layout, road_spacing, road_width, shape, center):
        """Add detailed individual buildings within blocks"""
        building_height_min, building_height_max = 8, 15
        building_width_min, building_width_max = 10, 20
        
        for i in range(road_width, self.grid_size - road_width, road_spacing):
            for j in range(road_width, self.grid_size - road_width, road_spacing):
                if layout[i, j] != 0:  # Skip if already occupied by road/water
                    continue
                
                if not self._is_in_city_bounds(i, j, shape):
                    continue
                
                # Divide block into smaller lots
                num_lots_h = np.random.randint(2, 4)
                num_lots_w = np.random.randint(2, 4)
                
                lot_height = (road_spacing - road_width) // num_lots_h
                lot_width = (road_spacing - road_width) // num_lots_w
                
                for lot_i in range(num_lots_h):
                    for lot_j in range(num_lots_w):
                        lot_start_i = i + lot_i * lot_height
                        lot_start_j = j + lot_j * lot_width
                        
                        # Add building or park
                        if np.random.random() < 0.85:  # 85% buildings
                            # Random building size
                            bldg_h = np.random.randint(building_height_min, min(building_height_max, lot_height - 2))
                            bldg_w = np.random.randint(building_width_min, min(building_width_max, lot_width - 2))
                            
                            zone_type = np.random.choice([2, 3, 5], p=[0.6, 0.3, 0.1])  # Res, Com, Ind
                            
                            for bi in range(bldg_h):
                                for bj in range(bldg_w):
                                    ii = lot_start_i + bi
                                    jj = lot_start_j + bj
                                    if 0 <= ii < self.grid_size and 0 <= jj < self.grid_size and layout[ii, jj] == 0:
                                        layout[ii, jj] = zone_type
                        else:  # Parks/green space
                            for bi in range(lot_height - 2):
                                for bj in range(lot_width - 2):
                                    ii = lot_start_i + bi
                                    jj = lot_start_j + bj
                                    if 0 <= ii < self.grid_size and 0 <= jj < self.grid_size and layout[ii, jj] == 0:
                                        layout[ii, jj] = 4
    
    def calculate_zone_percentages(self, layout=None):
        """Calculate percentage of each zone type in the city layout"""
        if layout is None:
            layout = self.generate_layout_grid()
        total_cells = self.grid_size * self.grid_size
        unique_zones, counts = np.unique(layout.astype(int), return_counts=True)
        
        zone_names = {
            0: 'Empty/Unallocated',
            1: 'Roads',
            2: 'Residential',
            3: 'Commercial',
            4: 'Parks & Green Space',
            5: 'Industrial',
            6: 'Water'
        }
        
        zones_percentage = {}
        for zone_id, count in zip(unique_zones, counts):
            percentage = (count / total_cells) * 100
            zone_name = zone_names.get(zone_id, f'Zone {zone_id}')
            zones_percentage[zone_name] = round(percentage, 2)
        
        return zones_percentage
    
    def create_visualization(self):
        """Create highly realistic city map visualization with proper roads"""
        layout = self.generate_layout_grid()
        zone_percentages = self.calculate_zone_percentages(layout)
        
        # Use portrait orientation for map
        fig, ax = plt.subplots(figsize=(14, 18), dpi=100)
        
        # Enhanced color scheme matching reference image
        colors = {
            0: '#E8D7C3',     # Empty - light beige
            1: '#696969',     # Roads - dark gray (main road color)
            2: '#E8714A',     # Residential - coral/orange-red
            3: '#F5D8A8',     # Commercial - light tan/cream
            4: '#6BBF59',     # Parks - vibrant green
            5: '#A78370',     # Industrial - brown-gray
            6: '#1E88E5'      # Water - blue
        }
        
        # Create map colors with vectorized operations for faster rendering
        zone_ids = layout.astype(int)
        max_zone_id = int(zone_ids.max())
        color_lut = np.zeros((max_zone_id + 1, 3), dtype=float)
        for zone_id, hex_color in colors.items():
            if zone_id <= max_zone_id:
                color_lut[zone_id] = self._hex_to_rgb(hex_color)
        colored_layout = color_lut[zone_ids]

        # Add subtle building texture/detail
        y_idx, x_idx = np.indices((self.grid_size, self.grid_size))
        checker = ((y_idx + x_idx) % 2 == 0)
        building_mask = np.isin(zone_ids, [2, 3, 5]) & checker
        colored_layout[building_mask] *= 0.95

        # Add park texture (darker greens scattered)
        park_texture_mask = (zone_ids == 4) & ((y_idx % 3 == 0) & (x_idx % 3 == 0))
        colored_layout[park_texture_mask] *= 0.85
        
        # Display the map
        ax.imshow(colored_layout, origin='upper', aspect='auto')
        
        # Add detailed road markings and lane lines
        self._add_road_markings(ax, layout)
        
        # Remove axis for clean map look
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Title
        title_text = f"{self.city} - Urban Development Plan ({self.shape.capitalize()})\n"
        title_text += f"Population: {self.population:,} | Area: {self.total_area} km² | Density: {self.calculate_density()}"
        ax.set_title(title_text, fontsize=12, fontweight='bold', pad=12, loc='left')
        
        # Zone distribution info box
        info_text = "Land Use Distribution:\n\n"
        for zone_name in sorted(zone_percentages.keys()):
            if zone_name == 'Water':
                continue  # Skip water if it's 0%
            pct = zone_percentages[zone_name]
            bar_len = int(pct / 3)
            bar = '█' * bar_len + '░' * (33 - bar_len)
            info_text += f"{zone_name}\n{bar} {pct}%\n"
        
        # Add info box
        props = dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.92, 
                    edgecolor='#333333', linewidth=1)
        ax.text(0.02, 0.25, info_text, transform=ax.transAxes, fontsize=7.5,
                verticalalignment='top', bbox=props, family='monospace', linespacing=1.4)
        
        # Add legend
        from matplotlib.patches import Rectangle as MapRectangle
        legend_y = 0.92
        legend_x = 0.02
        
        legend_items = [
            ('Roads & Streets', 1),
            ('Residential Areas', 2),
            ('Commercial', 3),
            ('Parks & Green', 4),
            ('Industrial', 5),
            ('Water Bodies', 6)
        ]
        
        for idx, (label, zone_id) in enumerate(legend_items):
            rgb = self._hex_to_rgb(colors[zone_id])
            rect = MapRectangle((legend_x, legend_y - idx * 0.04), 0.015, 0.015, 
                            transform=ax.transAxes, facecolor=rgb, edgecolor='black', linewidth=0.5)
            ax.add_patch(rect)
            ax.text(legend_x + 0.03, legend_y - idx * 0.04 + 0.005, label, 
                   transform=ax.transAxes, fontsize=7.5, va='center')
        
        # Add scale and compass
        ax.text(0.98, 0.02, 'N ↑', transform=ax.transAxes, fontsize=10,
                verticalalignment='bottom', horizontalalignment='right', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, pad=0.3))
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor='white',
                   edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
    
    def _add_road_markings(self, ax, layout):
        """Add proper road lane markings and intersections"""
        road_mask = layout == 1
        if not np.any(road_mask):
            return

        # Identify major rows/columns with dense road coverage
        row_counts = road_mask.sum(axis=1)
        col_counts = road_mask.sum(axis=0)
        main_h_roads = np.where(row_counts > self.grid_size * 0.3)[0]
        main_v_roads = np.where(col_counts > self.grid_size * 0.3)[0]

        # Draw markings only on continuous road segments so nothing is drawn on water.
        if len(main_h_roads) > 0:
            for row in main_h_roads:
                road_cols = np.where(road_mask[row, :])[0]
                if road_cols.size == 0:
                    continue
                splits = np.where(np.diff(road_cols) > 1)[0] + 1
                segments = np.split(road_cols, splits)
                for seg in segments:
                    ax.plot([seg[0], seg[-1]], [row, row], color='white',
                            linewidth=0.6, alpha=0.35, linestyle=(0, (4, 6)), zorder=1)

        if len(main_v_roads) > 0:
            for col in main_v_roads:
                road_rows = np.where(road_mask[:, col])[0]
                if road_rows.size == 0:
                    continue
                splits = np.where(np.diff(road_rows) > 1)[0] + 1
                segments = np.split(road_rows, splits)
                for seg in segments:
                    ax.plot([col, col], [seg[0], seg[-1]], color='white',
                            linewidth=0.6, alpha=0.35, linestyle=(0, (4, 6)), zorder=1)
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB normalized to 0-1"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
    
    def generate_report(self):
        """Generate a detailed analysis report"""
        density = self.calculate_density()
        road_width = self.determine_road_width()
        amenities = self.suggest_amenities()
        budget_data = self.calculate_budget()
        zone_percentages = self.calculate_zone_percentages()
        
        report = {
            "city": self.city,
            "total_area": f"{self.total_area} km²",
            "shape": self.shape.capitalize(),
            "population": f"{self.population:,}",
            "density": density,
            "temperature": f"{self.temperature}°C",
            "weather": self.weather,
            "road_width": f"Width Level: {road_width}/4",
            "road_description": self._get_road_description(road_width, density),
            "amenities": amenities,
            "recommendations": self._get_recommendations(density),
            "budget": {
                "total_millions": f"${budget_data['total_budget_millions']:,.2f} Million",
                "total_billions": f"${budget_data['total_budget_billions']:,.3f} Billion",
                "cost_per_sqkm": f"${budget_data['cost_per_sqkm']:,.2f} Million/km²"
            },
            "zone_distribution": zone_percentages,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return report
    
    def _get_road_description(self, width, density):
        """Get description for road width"""
        descriptions = {
            1: "Narrow roads suitable for low-traffic areas. Good for pedestrian-friendly communities.",
            2: "Medium-width roads for local traffic. Balanced between vehicle and pedestrian needs.",
            3: "Wider roads with multiple lanes. Designed for higher traffic volume and faster commute.",
            4: "Very wide roads (highways/motorways). Essential for metropolitan areas with heavy traffic."
        }
        return descriptions.get(width, "Standard roads")
    
    def _get_recommendations(self, density):
        """Get recommendations based on density"""
        recommendations = []
        
        # Shape-based recommendations
        shape = self.shape.lower()
        if shape == "circular":
            recommendations.append("Circular layout optimizes radial transit systems")
            recommendations.append("Central hub for main commercial/civic center ideal")
        elif shape == "triangle":
            recommendations.append("Triangular shape creates three strategic zones")
            recommendations.append("Develop major access points at three vertices")
        elif shape == "irregular":
            recommendations.append("Irregular shape requires adaptive infrastructure planning")
            recommendations.append("Focus on organic growth patterns and natural characteristics")
        
        if density == "Low":
            recommendations.append("Plan for agricultural areas and conservation zones")
            recommendations.append("Focus on community centers and local markets")
        elif density == "Medium":
            recommendations.append("Balance between commercial and residential development")
            recommendations.append("Invest in local public transportation")
        elif density == "High":
            recommendations.append("Implement multi-level parking structures")
            recommendations.append("Develop rapid transit systems (metro/buses)")
            recommendations.append("Maximize vertical development (high-rises)")
        else:
            recommendations.append("Implement advanced smart city infrastructure")
            recommendations.append("Develop comprehensive public transportation network")
            recommendations.append("Plan mixed-use developments")
        
        return recommendations
    
    def calculate_budget(self):
        """Calculate approximate construction budget based on area, density, and city"""
        # Base cost per square kilometer (in millions USD)
        base_cost_per_sqkm = {
            "Low": 50,      # Low density - less infrastructure
            "Medium": 150,  # Medium density - moderate infrastructure
            "High": 400,    # High density - extensive infrastructure
            "Very High": 800  # Very high density - intensive infrastructure
        }
        
        density = self.calculate_density()
        base_cost = base_cost_per_sqkm.get(density, 150)
        
        # Area calculation
        area_cost = base_cost * self.total_area
        
        # Shape multiplier (affects infrastructure complexity)
        shape_multipliers = {
            "square": 1.0,
            "rectangular": 1.1,
            "circular": 1.2,
            "triangle": 1.3,
            "irregular": 1.5
        }
        shape_mult = shape_multipliers.get(self.shape.lower(), 1.0)
        
        # City/region cost multiplier
        city_mult = self.city_cost_multipliers.get(self.city, self.city_cost_multipliers["Default"])
        
        # Weather/climate impact multiplier
        weather_multiplier = {
            "Sunny": 1.0,
            "Cloudy": 1.0,
            "Moderate": 1.0,
            "Rainy": 1.15,
            "Tropical": 1.2,
            "Snow": 1.3
        }
        weather_mult = weather_multiplier.get(self.weather, 1.0)
        
        # Road infrastructure multiplier
        road_multipliers = {
            "Basic": 1.2,       # Need to build more roads
            "Normal": 1.0,
            "Advanced": 0.9,    # Less infrastructure cost needed
            "Modern": 0.8       # Existing smart infrastructure
        }
        road_mult = road_multipliers.get(self.roads, 1.0)
        
        # Calculate final budget
        total_budget = area_cost * shape_mult * city_mult * weather_mult * road_mult
        
        return {
            "total_budget_millions": round(total_budget, 2),
            "total_budget_billions": round(total_budget / 1000, 3),
            "cost_per_sqkm": round(base_cost * shape_mult * city_mult * weather_mult * road_mult, 2),
            "density_factor": density,
            "shape_factor": shape_mult,
            "city_factor": city_mult,
            "weather_factor": weather_mult,
            "road_factor": road_mult
        }
